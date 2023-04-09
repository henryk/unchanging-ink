import vuetify from 'vite-plugin-vuetify'
import {ViteConfig} from '@nuxt/schema'

export default defineNuxtConfig({
    build: {
        transpile: ['vuetify'],
    },
    modules: [
        '@nuxtjs/i18n',
    ],
    hooks: {
        'vite:extendConfig': ({plugins}: ViteConfig) => {
            if (plugins) {
                plugins.push(
                    vuetify({}),
                )
            }
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
