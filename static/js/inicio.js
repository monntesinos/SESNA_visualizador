// ============================================================
// FUNCIONES DE INICIO
// Animación del contador de variables del CICM.
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

	// Funciones del contador: anima el número de variables al entrar en pantalla
	const numero = document.querySelector('.numero-destacado');
	if (!numero) return;

	const valorFinal = parseInt(numero.dataset.hasta, 10) || 0;
	const duracionMs = 1200;
	let animado = false;

	function animarContador() {
		const inicio = performance.now();

		function paso(ahora) {
			const progreso = Math.min((ahora - inicio) / duracionMs, 1);
			numero.textContent = Math.floor(progreso * valorFinal).toLocaleString('es-MX');
			if (progreso < 1) {
				requestAnimationFrame(paso);
			} else {
				numero.textContent = valorFinal.toLocaleString('es-MX');
			}
		}

		requestAnimationFrame(paso);
	}

	// Eventos: dispara la animación solo cuando la sección es visible
	const observador = new IntersectionObserver((entradas) => {
		entradas.forEach((entrada) => {
			if (entrada.isIntersecting && !animado) {
				animado = true;
				animarContador();
				observador.disconnect();
			}
		});
	}, { threshold: 0.5 });

	observador.observe(numero);
});
