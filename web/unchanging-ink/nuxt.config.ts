// https://nuxt.com/docs/api/configuration/nuxt-config
import vuetify from 'vite-plugin-vuetify'
import {ViteConfig} from '@nuxt/schema'

export default defineNuxtConfig({
    runtimeConfig: {
        public: {
            authority: "http://localhost:23230",
        },
    },
    build: {
        transpile: ['vuetify'],
    },
    modules: [
        '@nuxtjs/i18n',
    ],
    hooks: {
        'vite:extendConfig': (config: ViteConfig) => {
            config.plugins = [...(config.plugins ?? []), vuetify({})]
        },
    },
    i18n: {
        locales: [
            'en',
            'de',
        ],
        defaultLocale: 'de',
        vueI18n: {
            legacy: false,
            locale: 'de',
        },
    },
})
