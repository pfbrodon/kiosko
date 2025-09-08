// Sistema de búsqueda avanzada con cache
class BusquedaProductos {
    constructor() {
        this.cache = new Map();
        this.timeouts = new Map();
        this.initEventListeners();
    }

    initEventListeners() {
        // Búsqueda en tiempo real
        const searchInput = document.getElementById('busqueda-rapida');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }

        // Filtros avanzados
        const filtros = document.querySelectorAll('.filtro-avanzado');
        filtros.forEach(filtro => {
            filtro.addEventListener('change', () => {
                this.aplicarFiltros();
            });
        });
    }

    handleSearch(query) {
        // Limpiar timeout anterior
        if (this.timeouts.has('search')) {
            clearTimeout(this.timeouts.get('search'));
        }

        // Debounce de 300ms
        const timeout = setTimeout(() => {
            this.buscarProductos(query);
        }, 300);

        this.timeouts.set('search', timeout);
    }

    async buscarProductos(query) {
        if (query.length < 2) {
            this.ocultarResultados();
            return;
        }

        // Verificar cache
        const cacheKey = this.getCacheKey(query);
        if (this.cache.has(cacheKey)) {
            this.mostrarResultados(this.cache.get(cacheKey));
            return;
        }

        try {
            this.mostrarCargando();
            
            const params = new URLSearchParams({
                q: query,
                categoria: document.getElementById('categoria-filtro')?.value || '',
                proveedor: document.getElementById('proveedor-filtro')?.value || ''
            });

            const response = await fetch(`/productos/buscar/?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                // Guardar en cache por 2 minutos
                this.cache.set(cacheKey, data.productos);
                setTimeout(() => this.cache.delete(cacheKey), 120000);
                
                this.mostrarResultados(data.productos);
            } else {
                this.mostrarError('Error en la búsqueda');
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarError('Error de conexión');
        }
    }

    getCacheKey(query) {
        const categoria = document.getElementById('categoria-filtro')?.value || '';
        const proveedor = document.getElementById('proveedor-filtro')?.value || '';
        return `${query}_${categoria}_${proveedor}`;
    }

    mostrarResultados(productos) {
        const contenedor = document.getElementById('resultados-busqueda');
        if (!contenedor) return;

        if (productos.length === 0) {
            contenedor.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-search"></i> No se encontraron productos
                </div>
            `;
        } else {
            const html = productos.map(producto => `
                <div class="producto-resultado border-bottom py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${producto.nombre}</h6>
                            <small class="text-muted">
                                ${producto.codigo} - ${producto.categoria}
                                ${producto.proveedor ? ` - ${producto.proveedor}` : ''}
                            </small>
                        </div>
                        <div class="text-end">
                            <div class="fw-bold text-primary">$${producto.precio}</div>
                            <small class="text-muted">Stock: ${producto.stock}</small>
                        </div>
                    </div>
                </div>
            `).join('');

            contenedor.innerHTML = html;
        }

        contenedor.style.display = 'block';
    }

    mostrarCargando() {
        const contenedor = document.getElementById('resultados-busqueda');
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="text-center py-3">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">Buscando...</span>
                    </div>
                    <small class="ms-2">Buscando productos...</small>
                </div>
            `;
            contenedor.style.display = 'block';
        }
    }

    mostrarError(mensaje) {
        const contenedor = document.getElementById('resultados-busqueda');
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${mensaje}
                </div>
            `;
        }
    }

    ocultarResultados() {
        const contenedor = document.getElementById('resultados-busqueda');
        if (contenedor) {
            contenedor.style.display = 'none';
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    aplicarFiltros() {
        // Limpiar cache cuando cambien los filtros
        this.cache.clear();
        
        // Rehacer búsqueda si hay texto
        const searchInput = document.getElementById('busqueda-rapida');
        if (searchInput && searchInput.value.length >= 2) {
            this.buscarProductos(searchInput.value);
        }
    }
}

// Paginación AJAX
class PaginacionAjax {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        // Interceptar clics en enlaces de paginación
        document.addEventListener('click', (e) => {
            if (e.target.matches('.page-link-ajax')) {
                e.preventDefault();
                this.cargarPagina(e.target.href);
            }
        });
    }

    async cargarPagina(url) {
        try {
            this.mostrarCargando();

            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const html = await response.text();
                this.actualizarContenido(html);
                
                // Actualizar URL sin recargar página
                window.history.pushState({}, '', url);
            } else {
                this.mostrarError('Error al cargar la página');
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarError('Error de conexión');
        }
    }

    mostrarCargando() {
        const contenedor = document.getElementById('contenedor-productos');
        if (contenedor) {
            contenedor.style.opacity = '0.5';
            contenedor.style.pointerEvents = 'none';
        }
    }

    actualizarContenido(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Actualizar tabla de productos
        const nuevaTabla = doc.querySelector('#contenedor-productos');
        const contenedorActual = document.getElementById('contenedor-productos');
        
        if (nuevaTabla && contenedorActual) {
            contenedorActual.innerHTML = nuevaTabla.innerHTML;
            contenedorActual.style.opacity = '1';
            contenedorActual.style.pointerEvents = 'auto';
        }

        // Actualizar paginación
        const nuevaPaginacion = doc.querySelector('.pagination');
        const paginacionActual = document.querySelector('.pagination');
        
        if (nuevaPaginacion && paginacionActual) {
            paginacionActual.innerHTML = nuevaPaginacion.innerHTML;
        }
    }

    mostrarError(mensaje) {
        const contenedor = document.getElementById('contenedor-productos');
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${mensaje}
                </div>
            `;
            contenedor.style.opacity = '1';
            contenedor.style.pointerEvents = 'auto';
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new BusquedaProductos();
    new PaginacionAjax();
    
    console.log('🚀 Sistemas de búsqueda y paginación AJAX inicializados');
});
