import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'
import {
  VAlert,
  VApp,
  VAppBar,
  VAppBarNavIcon,
  VAvatar,
  VBtn,
  VCard,
  VCardActions,
  VCardSubtitle,
  VCardText,
  VCardTitle,
  VCol,
  VContainer,
  VExpansionPanel,
  VExpansionPanelText,
  VExpansionPanelTitle,
  VExpansionPanels,
  VFileInput,
  VFooter,
  VIcon,
  VList,
  VListItem,
  VListItemTitle,
  VMain,
  VNavigationDrawer,
  VProgressLinear,
  VRow,
  VSelect,
  VSnackbar,
  VSpacer,
  VTab,
  VTabs,
  VTextField,
  VTextarea,
  VTimeline,
  VTimelineItem,
  VToolbarTitle,
  VWindow,
  VWindowItem,
  VExpandTransition,
} from 'vuetify/components'
import * as directives from 'vuetify/directives'
import colors from 'vuetify/util/colors'

const theme = {
  defaultTheme: 'light',
  themes: {
    light: {
      colors: {
        primary: colors.cyan.darken2,
        accent: colors.deepPurple.darken1,
        secondary: colors.blue.darken1,
        info: colors.indigo.lighten1,
        warning: colors.amber.base,
        error: colors.deepOrange.accent4,
        success: colors.green.accent3,
      },
    },
  },
}

export default defineNuxtPlugin((nuxtApp) => {
  const vuetify = createVuetify({
    // Ensure consistent SSR/client rendering for breakpoint-dependent components
    ssr: true,
    components: {
      VAlert,
      VApp,
      VAppBar,
      VAppBarNavIcon,
      VAvatar,
      VBtn,
      VCard,
      VCardActions,
      VCardSubtitle,
      VCardText,
      VCardTitle,
      VCol,
      VContainer,
      VExpansionPanel,
      VExpansionPanelText,
      VExpansionPanelTitle,
      VExpansionPanels,
      VFileInput,
      VFooter,
      VIcon,
      VList,
      VListItem,
      VListItemTitle,
      VMain,
      VNavigationDrawer,
      VProgressLinear,
      VRow,
      VSelect,
      VSnackbar,
      VSpacer,
      VTab,
      VTabs,
      VTextField,
      VTextarea,
      VTimeline,
      VTimelineItem,
      VToolbarTitle,
      VWindow,
      VWindowItem,
      VExpandTransition,
    },
    directives,
    icons: {
      defaultSet: 'mdi',
      aliases,
      sets: { mdi },
    },
    // Configure display service so SSR doesn't assume "mobile" widths
    display: {
      mobileBreakpoint: 'sm',
      thresholds: { xs: 0, sm: 600, md: 960, lg: 1280, xl: 1920 },
      // Approximate a desktop viewport on the server to avoid hydration mismatches
      ssr: {
        clientWidth: 1280,
        clientHeight: 800,
      },
    },
    theme,
  })

  nuxtApp.vueApp.use(vuetify)
})
