import 'vuetify/styles'
import {createVuetify} from 'vuetify'
import {aliases, mdi} from 'vuetify/iconsets/mdi-svg'

export default defineNuxtPlugin(({vueApp}) => {
    const vuetify = createVuetify({
        ssr: true,
        icons: {
            defaultSet: 'mdi',
            aliases,
            sets: {
                mdi,
            },
        },

    })

    vueApp.use(vuetify)
})