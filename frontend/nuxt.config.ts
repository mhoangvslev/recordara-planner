// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', "nuxt-plotly", '@nuxtjs/i18n'],
  vite: {
    optimizeDeps: {
      include: ["plotly.js-dist-min"],
    },
  },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      dataPath: '../backend/output/assignments.csv'
    }
  },
  i18n: {
    locales: [
      // { code: 'en', name: 'English', file: 'en.json' },
      { code: 'fr', name: 'Français', file: 'fr.json' }
    ],
    defaultLocale: 'fr',
    langDir: 'locales/',
    strategy: 'prefix_except_default',
    lazy: true,
    loadLanguagesAsync: true,
  },
  vueI18n: {
    fallbackLocale: 'en',
  }
})
