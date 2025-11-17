export default defineNuxtConfig({
  devtools: {
    enabled: false,
  },
  app: {
    head: {
      titleTemplate: '%s - unchanging.ink',
      title: 'unchanging.ink',
      htmlAttrs: {
        lang: 'de',
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { hid: 'description', name: 'description', content: '' },
      ],
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
    },
  },
  css: [
    'vuetify/styles',
    '@fontsource/roboto/400.css',
    '@fontsource/roboto/500.css',
  ],
  modules: ['@nuxtjs/i18n', '@nuxt/content', '@sentry/nuxt'],
  runtimeConfig: {
    public: {
      authority: process.env.AUTHORITY || '',
      sentryDsn:
        process.env.SENTRY_DSN ||
        'https://26453d4c0df842bdbe54069d5d23452c@sentry.digitalwolff.de/11',
    },
  },
  i18n: {
    locales: [
      { code: 'en', name: 'English' },
      { code: 'de', name: 'Deutsch' },
    ],
    defaultLocale: 'en',
    detectBrowserLanguage: {
      useCookie: false,
    },
    vueI18n: './i18n.config.js',
  },
  sentry: {
    dsn:
      process.env.SENTRY_DSN ||
      'https://26453d4c0df842bdbe54069d5d23452c@sentry.digitalwolff.de/11',
    tracesSampleRate: 1.0,
  },
  build: {
    transpile: ['vuetify'],
  },
  vite: {
    resolve: {
      alias: {
        cbor: 'cbor-web',
      },
    },
    server: {
      watch: {
        usePolling: true,
      },
    },
  },
})
