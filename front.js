document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("serviceForm");
  const status = document.getElementById("formStatus");

  if (!form || !status) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const name = String(formData.get("name") || "Cliente").trim();
    const email = String(formData.get("email") || "").trim();
    const service = String(formData.get("service") || "Serviço solicitado").trim();
    const message = String(formData.get("message") || "").trim();

    status.textContent = "Enviando sua solicitação...";

    try {
      const apiUrl = window.location.port === "5501"
        ? "http://127.0.0.1:5000/api/contact"
        : "/api/contact";
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, service, message }),
      });

      const responseText = await response.text();
      let result = {};

      try {
        result = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error("O servidor retornou uma resposta inválida. Verifique se o backend está em execução.");
      }

      if (!response.ok) {
        throw new Error(result.error || "Não foi possível enviar a solicitação.");
      }

      status.textContent = "Solicitação enviada com sucesso. Em breve entraremos em contato.";
      form.reset();
    } catch (error) {
      status.textContent = error.message || "Não foi possível enviar a solicitação.";
      console.error(error);
    }
  });
});
