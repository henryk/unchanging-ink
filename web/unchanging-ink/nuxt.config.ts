// https://nuxt.com/docs/api/configuration/nuxt-config
import vuetify from 'vite-plugin-vuetify'
import {ViteConfig} from '@nuxt/schema'
import { resolve } from 'pathe'

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
        '@nuxt/content'
    ],
    hooks: {
        'vite:extendConfig': (config: ViteConfig) => {
            config.plugins = [...(config.plugins ?? []), vuetify({})]
        },
    },
    content: {
        doc: {
            driver: 'fs',
            prefix: '/doc',
            base: resolve(__dirname + '/../../doc')
        },
    }
})
