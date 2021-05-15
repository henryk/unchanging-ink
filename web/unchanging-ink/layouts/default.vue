<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" :clipped="clipped" fixed app>
      <v-list>
        <v-list-item
          v-for="(item, i) in items"
          :key="i"
          :to="item.to"
          router
          exact
        >
          <v-list-item-action>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title v-text="item.title" />
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar :clipped-left="clipped" fixed app>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title v-text="title" />
      <v-spacer />
    </v-app-bar>
    <v-main>
      <v-container>
        <nuxt />
      </v-container>
    </v-main>
    <v-footer :absolute="!fixed" app>
      <span>&copy; 2021</span>
      <v-spacer></v-spacer>
      <v-icon class="px-2">{{ mdiTranslate }}</v-icon>
      <nuxt-link
        v-for="locale in availableLocales"
        :key="locale.code"
        :to="switchLocalePath(locale.code)"
        >{{ locale.name }}</nuxt-link
      >
    </v-footer>
  </v-app>
</template>

<script>
import { mdiHome, mdiBookOpenVariant, mdiTranslate } from '@mdi/js'

export default {
  data() {
    return {
      mdiTranslate,
      clipped: false,
      drawer: false,
      fixed: false,
      items: [
        {
          icon: mdiHome,
          title: this.$t('homepage'),
          to: '/',
        },
        {
          icon: mdiBookOpenVariant,
          title: 'Documentation',
          to: '/doc/',
        },
      ],
      right: true,
      rightDrawer: false,
      title: 'unchanging.ink -- ' + this.$t('timestampService'),
    }
  },
  computed: {
    availableLocales() {
      return this.$i18n.locales.filter((i) => i.code !== this.$i18n.locale)
    },
  },
}
</script>
<i18n lang="yaml">
de:
  timestampService: Zeitstempeldienst
  homepage: Startseite
en:
  timestampService: Timestamp Service
  homepage: Home Page
</i18n>
