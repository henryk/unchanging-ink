import { Plugin } from 'vite'
import vuetify from 'vite-plugin-vuetify'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'

export default defineAppConfig({
    title: 'unchanging.ink',
    titleTemplate: '%s - unchanging.ink',
    head: {
        htmlAttrs: {
            lang: 'en',
        },
        meta: [
            {charset: 'utf-8'},
            {name: 'viewport', content: 'width=device-width, initial-scale=1'},
            {hid: 'description', name: 'description', content: ''},
        ],
        link: [{rel: 'icon', type: 'image/x-icon', href: '/favicon.ico'}],

    },
    css: ['@fontsource/roboto', 'vuetify/styles/main.sass'],
    build: {
        transpile: ['vuetify'],
    },
    hooks: {
        'vite:extendConfig': (config: { plugins: Plugin[][] }) => {
            config.plugins.push(
                vuetify(),
            )
            config.plugins.push(
                VueI18nPlugin({})
            )
        },
    },
})