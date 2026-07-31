// ============================================================
// FUNCIONES DEL FORMULARIO DE CONTACTO
// Validaciones en cliente antes de enviar el mensaje.
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

	const formulario = document.getElementById('form-contacto');
	const mensajeEnvio = document.getElementById('mensaje-envio');
	if (!formulario) return;

	// Validaciones: reglas por campo
	const reglas = {
		'input-nombre': (valor) => valor.trim().length > 0 || 'Escribe tu nombre.',
		'input-correo': (valor) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor.trim()) || 'Escribe un correo válido.',
		'input-asunto': (valor) => valor.trim().length > 0 || 'Escribe el asunto de tu mensaje.',
		'txt-mensaje': (valor) => valor.trim().length >= 10 || 'Tu mensaje debe tener al menos 10 caracteres.'
	};

	function validarCampo(campo) {
		const grupo = campo.closest('.grupo-input');
		const mensajeError = grupo.querySelector('.mensaje-error');
		const resultado = reglas[campo.id](campo.value);

		if (resultado === true) {
			grupo.classList.remove('campo-invalido');
			mensajeError.textContent = '';
			return true;
		}

		grupo.classList.add('campo-invalido');
		mensajeError.textContent = resultado;
		return false;
	}

	// Eventos de botones: validar cada campo al perder el foco
	Object.keys(reglas).forEach((id) => {
		const campo = document.getElementById(id);
		campo.addEventListener('blur', () => validarCampo(campo));
	});

	// Eventos de botones: validar todo el formulario antes de enviarlo
	formulario.addEventListener('submit', (evento) => {
		let formularioValido = true;

		Object.keys(reglas).forEach((id) => {
			const campo = document.getElementById(id);
			if (!validarCampo(campo)) {
				formularioValido = false;
			}
		});

		if (!formularioValido) {
			evento.preventDefault();
			mensajeEnvio.hidden = true;
			return;
		}

		mensajeEnvio.textContent = 'Abriendo tu cliente de correo para enviar el mensaje...';
		mensajeEnvio.hidden = false;
	});
});
