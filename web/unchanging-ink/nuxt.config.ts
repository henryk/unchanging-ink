import vuetify from 'vite-plugin-vuetify'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'

export default defineNuxtConfig({
    vite: {
        plugins: [
            vuetify(),
            VueI18nPlugin({
            }),
        ]
    },
})
