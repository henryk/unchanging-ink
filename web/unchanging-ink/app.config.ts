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
})