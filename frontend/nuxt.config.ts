// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', "nuxt-plotly", '@nuxtjs/i18n'],
  
  // GitHub Pages configuration
  ssr: false, // Enable static generation
  nitro: {
    prerender: {
      routes: ['/']
    }
  },
  
  // Set base URL for GitHub Pages
  app: {
    baseURL: process.env.NODE_ENV === 'production' ? '/recordara-planner/' : '/',
    buildAssetsDir: '/_nuxt/'
  },
  vite: {
    optimizeDeps: {
      include: ["plotly.js-dist-min"],
    },
  },
  css: ['~/assets/css/main.css'],
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
