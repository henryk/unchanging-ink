export default defineI18nConfig(() => ({
  legacy: false,
  globalInjection: true,
  fallbackLocale: 'en',
  messages: {
    de: {
      liveView: 'Live-Ansicht',
    },
    en: {
      liveView: 'Live View',
    },
  },
}))
