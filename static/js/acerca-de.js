// ============================================================
// FUNCIONES DE ACERCA DE
// Usado dentro de inicio.html: solo controla el menú cuadrado de
// Ejes del Plan Nacional Anticorrupción (mostrar/ocultar panel al clic).




     // LA MAYOR PARTE DE INICIO NO NECESITA JAVA GRACIAS A DIOS SOLO LOS EJES//
// NOTA: el menú de pestañas (Qué es/Objetivo/Misión/Visión) y el
// carrusel (Antecedentes/Origen/Beneficios) se eliminaron a petición;
// esas secciones ahora son estáticas (tríptico y línea del tiempo,
// ver inicio.html) y no necesitan JavaScript.
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

	// Eventos de botones: menú cuadrado de Ejes del Plan Nacional Anticorrupción
	const botonesEje = document.querySelectorAll('.eje-cuadro');
	botonesEje.forEach((boton) => {
		boton.addEventListener('click', () => {
			const idEje = boton.dataset.eje;

			botonesEje.forEach((b) => b.classList.remove('activo'));
			document.querySelectorAll('.eje-panel').forEach((panel) => panel.classList.remove('activo'));

			boton.classList.add('activo');
			document.getElementById(idEje).classList.add('activo');
		});
	});
});
