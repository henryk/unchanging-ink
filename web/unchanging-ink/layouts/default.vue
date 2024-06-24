<template>
  <v-app>
    <v-navigation-drawer v-model="drawer">
      <v-list>
        <v-list-item v-for="item in navItems" :key="item.to" :to="item.to">
          <template v-slot:prepend>
            <v-icon color="primary">{{ item.icon }}</v-icon>
          </template>

          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-toolbar-title>unchanging.ink</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <slot />
    </v-main>

    <v-footer app>
      <v-spacer /><NuxtLink
        to="https://github.com/henryk/unchanging-ink"
        color="primary"
        ><v-icon>{{ mdiGithub }}</v-icon></NuxtLink
      >
    </v-footer>
  </v-app>
</template>
<script lang="ts" setup>
import { mdiGithub, mdiHome } from "@mdi/js"

const { t } = useI18n()

const drawer = ref(true)
const navItems = [
  {
    icon: mdiHome,
    title: t("homepage"),
    to: "/",
  },
  /* FIXME Doesn't work
    {
        icon: mdiBookOpenVariant,
        title: 'documentation',
        to: '/doc',
    },
    */
]
</script>
<i18n lang="json5">
{
  de: {
    homepage: "Startseite",
  },
}
</i18n>
