// ============================================================
// FUNCIONES DEL BUSCADOR CIUDADANO
// Muestra/oculta los filtros de Estado y Municipio según el
// nivel de gobierno seleccionado (Todos / Federal / Estatal).
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

	const radiosNivelGobierno = document.querySelectorAll('input[name="nivel_gobierno"]');
	const contenedorEstado = document.getElementById('contenedor-estado');
	const contenedorMunicipio = document.getElementById('contenedor-municipio');
	const filtroEstado = document.getElementById('filtro-estado');

	if (!radiosNivelGobierno.length || !contenedorEstado || !contenedorMunicipio || !filtroEstado) {
		return;
	}

	// Muestra u oculta el filtro de Estado según el radio seleccionado.
	function actualizarFiltroEstado() {
		const seleccionado = document.querySelector('input[name="nivel_gobierno"]:checked');
		const esEstatal = seleccionado && seleccionado.value === 'estatal';

		contenedorEstado.classList.toggle('oculto', !esEstatal);

		// Si se deja de mostrar el filtro de Estado, se limpia y se
		// oculta también el de Municipio para no dejar filtros "huérfanos".
		if (!esEstatal) {
			filtroEstado.value = '';
			contenedorMunicipio.classList.add('oculto');
		}
	}

	// Muestra u oculta el filtro de Municipio según si ya se eligió un Estado.
	function actualizarFiltroMunicipio() {
		contenedorMunicipio.classList.toggle('oculto', filtroEstado.value === '');
	}

	radiosNivelGobierno.forEach(function (radio) {
		radio.addEventListener('change', actualizarFiltroEstado);
	});

	filtroEstado.addEventListener('change', actualizarFiltroMunicipio);

	// Estado inicial al cargar la página (por si el navegador
	// recuerda una selección previa del formulario).
	actualizarFiltroEstado();
	actualizarFiltroMunicipio();
});
