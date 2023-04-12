// https://nuxt.com/docs/api/configuration/nuxt-config
import vuetify from 'vite-plugin-vuetify'
import {ViteConfig} from '@nuxt/schema'

export default defineNuxtConfig({
    runtimeConfig: {
        public: {
            authority: "http://localhost:23230",
        },
    },
    css: ['@fontsource/roboto', 'vuetify/styles/main.sass'],
    app: {
        head: {
            htmlAttrs: {
                lang: 'de',
            },
            meta: [
                {charset: 'utf-8'},
                {name: 'viewport', content: 'width=device-width, initial-scale=1'},
            ],
            link: [{rel: 'icon', type: 'image/x-icon', href: '/favicon.ico'}],
            title: 'unchanging.ink',
            titleTemplate: '%s - unchanging.ink',
        },
    },
    build: {
        transpile: ['vuetify'],
    },
    modules: [
        '@nuxtjs/i18n',
        '@vueuse/nuxt',
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
