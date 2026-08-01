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

document.addEventListener('DOMContentLoaded', () => {
    const btnAbrir = document.getElementById('btn-abrir-buscador');
    const modal = document.getElementById('modal-buscador');
    const btnCerrar = document.getElementById('btn-cerrar-buscador');

    if(btnAbrir && modal && btnCerrar) {
        // Abrir modal
        btnAbrir.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.add('modal-activo');
            modal.setAttribute('aria-hidden', 'false');
        });

        // Cerrar modal desde la X
        btnCerrar.addEventListener('click', () => {
            modal.classList.remove('modal-activo');
            modal.setAttribute('aria-hidden', 'true');
        });

        // Cerrar modal al hacer clic en el fondo gris
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('modal-activo');
                modal.setAttribute('aria-hidden', 'true');
            }
        });
    }
});