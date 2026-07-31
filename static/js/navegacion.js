// ============================================================
// NAVEGACIÓN - CICM
// Menú responsive (hamburguesa en móvil) y resaltado del
// enlace activo según la página actual. Compartido por todas
// las pestañas del sitio.
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

	// Navegación: alternar menú móvil
	const botonMenu = document.querySelector('.boton-menu-movil');
	const menuPrincipal = document.getElementById('menu-principal');

	if (botonMenu && menuPrincipal) {
		botonMenu.addEventListener('click', () => {
			const abierto = menuPrincipal.classList.toggle('menu-abierto');
			botonMenu.setAttribute('aria-expanded', abierto);
		});
	}

	// Navegación: resaltar el enlace correspondiente a la página actual
	const paginaActual = window.location.pathname.split('/').pop() || 'inicio.html';
	document.querySelectorAll('#menu-principal a').forEach((enlace) => {
		const destino = enlace.getAttribute('href');
		if (destino === paginaActual) {
			enlace.setAttribute('aria-current', 'page');
		}
	});
});
