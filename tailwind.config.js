/** Build único para generar src/api/static/css/tailwind.css — ver README. */
module.exports = {
  content: ["./src/api/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        marca: {
          DEFAULT: "var(--color-primario)",
          hover: "var(--color-primario-hover)",
          suave: "var(--color-primario-suave)",
        },
        cian: {
          DEFAULT: "var(--color-secundario)",
          suave: "var(--color-secundario-suave)",
        },
        acento: "var(--color-acento)",
        aviso: "var(--color-aviso)",
        alerta: "var(--color-alerta)",
      },
    },
  },
  plugins: [],
};
