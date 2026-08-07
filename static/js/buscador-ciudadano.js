// ============================================================
// FUNCIONES DEL BUSCADOR CIUDADANO
// - Muestra/oculta el filtro de Estado según el nivel de
//   gobierno seleccionado (Todos / Federal / Estatal).
// - Habilita/deshabilita el botón "Ver mapa" según el mismo
//   criterio, y controla el cambio entre vista Tabla / Mapa.
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

	// --- Contador de resultados animado (cuenta hacia arriba desde 0) ---
	(function animarContador() {
		const elementoContador = document.getElementById('contador-numero');
		if (!elementoContador) {
			return;
		}

		const total = parseInt(elementoContador.getAttribute('data-total'), 10) || 0;
		const prefiereMenosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

		if (prefiereMenosMovimiento || total === 0) {
			elementoContador.textContent = total.toLocaleString('es-MX');
			return;
		}

		const duracionMs = 600;
		const inicio = performance.now();

		function paso(ahora) {
			const progreso = Math.min((ahora - inicio) / duracionMs, 1);
			// Easing suave de salida (desacelera al final)
			const progresoSuavizado = 1 - Math.pow(1 - progreso, 3);
			const valorActual = Math.round(progresoSuavizado * total);
			elementoContador.textContent = valorActual.toLocaleString('es-MX');

			if (progreso < 1) {
				requestAnimationFrame(paso);
			}
		}

		requestAnimationFrame(paso);
	})();

	// --- Autocompletado de la barra de búsqueda de variables ---
	(function inicializarAutocompletado() {
		const formularioBusqueda = document.getElementById('formulario-busqueda-texto');
		const inputBusqueda = document.getElementById('busqueda-texto');
		const listaSugerencias = document.getElementById('lista-sugerencias');

		if (!formularioBusqueda || !inputBusqueda || !listaSugerencias) {
			return;
		}

		let temporizadorDebounce = null;
		let indiceResaltado = -1;

		function ocultarSugerencias() {
			listaSugerencias.classList.add('oculto');
			listaSugerencias.innerHTML = '';
			inputBusqueda.setAttribute('aria-expanded', 'false');
			indiceResaltado = -1;
		}

		function mostrarSugerencias(nombres) {
			listaSugerencias.innerHTML = '';

			if (!nombres.length) {
				ocultarSugerencias();
				return;
			}

			nombres.forEach(function (nombre) {
				const item = document.createElement('li');
				item.textContent = nombre;
				item.setAttribute('role', 'option');
				item.addEventListener('click', function () {
					inputBusqueda.value = nombre;
					ocultarSugerencias();
					formularioBusqueda.submit(); // Clic en sugerencia = buscar automáticamente
				});
				listaSugerencias.appendChild(item);
			});

			listaSugerencias.classList.remove('oculto');
			inputBusqueda.setAttribute('aria-expanded', 'true');
			indiceResaltado = -1;
		}

		async function buscarSugerencias(texto) {
			try {
				const respuesta = await fetch('/api/sugerencias-variables?q=' + encodeURIComponent(texto));
				if (!respuesta.ok) {
					ocultarSugerencias();
					return;
				}
				const nombres = await respuesta.json();
				mostrarSugerencias(nombres);
			} catch (error) {
				ocultarSugerencias();
			}
		}

		inputBusqueda.addEventListener('input', function () {
			const texto = inputBusqueda.value.trim();

			clearTimeout(temporizadorDebounce);

			if (texto.length < 2) {
				ocultarSugerencias();
				return;
			}

			// Espera 300ms después de que el usuario deja de escribir
			temporizadorDebounce = setTimeout(function () {
				buscarSugerencias(texto);
			}, 300);
		});

		// Navegación con teclado (flechas + Enter)
		inputBusqueda.addEventListener('keydown', function (evento) {
			const items = listaSugerencias.querySelectorAll('li');
			if (!items.length || listaSugerencias.classList.contains('oculto')) {
				return;
			}

			if (evento.key === 'ArrowDown') {
				evento.preventDefault();
				indiceResaltado = (indiceResaltado + 1) % items.length;
			} else if (evento.key === 'ArrowUp') {
				evento.preventDefault();
				indiceResaltado = (indiceResaltado - 1 + items.length) % items.length;
			} else if (evento.key === 'Enter' && indiceResaltado >= 0) {
				evento.preventDefault();
				items[indiceResaltado].click();
				return;
			} else if (evento.key === 'Escape') {
				ocultarSugerencias();
				return;
			} else {
				return;
			}

			items.forEach(function (item, i) {
				item.classList.toggle('resaltado', i === indiceResaltado);
			});
		});

		// Cerrar la lista si se hace clic fuera del buscador
		document.addEventListener('click', function (evento) {
			if (!formularioBusqueda.contains(evento.target)) {
				ocultarSugerencias();
			}
		});
	})();

	const radiosNivelGobierno = document.querySelectorAll('input[name="nivel_gobierno"]');
	const contenedorEstado = document.getElementById('contenedor-estado');
	const filtroEstado = document.getElementById('filtro-estado');

	const botonVerTabla = document.getElementById('boton-ver-tabla');
	const botonVerMapa = document.getElementById('boton-ver-mapa');
	const contenedorTabla = document.getElementById('contenedor-tabla');
	const contenedorMapa = document.getElementById('contenedor-mapa');

	// --- Mostrar/ocultar filtro de Estado según nivel de gobierno ---
	function actualizarFiltroEstado() {
		const seleccionado = document.querySelector('input[name="nivel_gobierno"]:checked');
		const esEstatal = seleccionado && seleccionado.value === 'estatal';

		if (contenedorEstado) {
			contenedorEstado.classList.toggle('oculto', !esEstatal);
			if (!esEstatal && filtroEstado) {
				filtroEstado.value = '';
			}
		}

		// El botón "Ver mapa" solo se habilita en nivel Estatal/Municipal.
		// (Todavía sin funcionalidad real detrás, solo el estado habilitado/deshabilitado.)
		if (botonVerMapa) {
			botonVerMapa.disabled = !esEstatal;
			if (!esEstatal) {
				cambiarVista('tabla');
			}
		}
	}

	// --- Cambiar entre vista Tabla / Mapa ---
	function cambiarVista(vista) {
		if (!botonVerTabla || !botonVerMapa || !contenedorTabla || !contenedorMapa) {
			return;
		}

		const esMapa = vista === 'mapa';

		contenedorTabla.classList.toggle('oculto', esMapa);
		contenedorMapa.classList.toggle('oculto', !esMapa);

		botonVerTabla.classList.toggle('activo', !esMapa);
		botonVerMapa.classList.toggle('activo', esMapa);
	}

	if (radiosNivelGobierno.length) {
		radiosNivelGobierno.forEach(function (radio) {
			radio.addEventListener('change', actualizarFiltroEstado);
		});
		// Estado inicial al cargar la página (por si el navegador
		// recuerda una selección previa del formulario).
		actualizarFiltroEstado();
	}

	if (botonVerTabla && botonVerMapa) {
		botonVerTabla.addEventListener('click', function () { cambiarVista('tabla'); });
		botonVerMapa.addEventListener('click', function () {
			if (!botonVerMapa.disabled) {
				cambiarVista('mapa');
			}
		});
	}
});
