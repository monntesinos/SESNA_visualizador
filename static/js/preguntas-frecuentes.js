// ============================================================
// FUNCIONES DE PREGUNTAS FRECUENTES
// Acordeón: muestra/oculta la respuesta al hacer clic en la
// pregunta y mantiene el atributo aria-expanded actualizado.
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

	// Eventos de botones: alternar cada pregunta del acordeón
	document.querySelectorAll('.faq-pregunta').forEach((boton) => {
		boton.addEventListener('click', () => {
			const respuesta = document.getElementById(boton.getAttribute('aria-controls'));
			const expandido = boton.getAttribute('aria-expanded') === 'true';

			boton.setAttribute('aria-expanded', String(!expandido));
			respuesta.hidden = expandido;
		});
	});
});
