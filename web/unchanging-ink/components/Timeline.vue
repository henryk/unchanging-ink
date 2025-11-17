<template>
  <v-card
    :loading="true"
    @mouseenter="pauseMover = true"
    @mouseleave="pauseMover = false"
  >
    <template #loader>
      <v-progress-linear
        :model-value="!paused ? progressToNext : null"
      ></v-progress-linear>
    </template>
    <v-card-title class="headline">
      {{ $t('liveView') }}
      <v-spacer></v-spacer>
      <v-icon v-if="paused" :icon="mdiPause"></v-icon>
      <v-icon v-else :icon="mdiPlay"></v-icon>
    </v-card-title>
    <v-card-text style="max-height: 35em; overflow-y: hidden">
      <v-timeline v-show="displayItems.length" density="compact">
        <transition-group name="slide-y-transition">
          <timeline-item-card
            v-for="item in displayItems"
            :key="item.time"
            :item="item"
          ></timeline-item-card>
        </transition-group>
      </v-timeline>
    </v-card-text>
  </v-card>
</template>

<script>
import { mdiPause, mdiPlay } from '@mdi/js'
import TimelineItemCard from './TimelineItemCard'

export default {
  name: 'TimelineCard',
  components: { TimelineItemCard },
  props: {
    progressToNext: {
      type: Number,
      required: false,
      default: null,
    },
    items: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      mdiPause,
      mdiPlay,
      pausedItems: [],
      pauseMover: false,
      pauseBackground: false,
    }
  },
  computed: {
    displayItems() {
      return this.paused ? this.pausedItems : this.items
    },
    paused() {
      return this.pauseMover || this.pauseBackground
    },
  },
  watch: {
    paused(newVal) {
      if (newVal) {
        this.pausedItems = [...this.items]
      }
    },
  },
  mounted() {
    document.addEventListener(
      'visibilitychange',
      this.handleVisibilityChange,
      false
    )
  },
  methods: {
    handleVisibilityChange() {
      this.pauseBackground = document.hidden
    },
  },
}
</script>

<style scoped></style>
<i18n lang="yaml">
de:
  liveView: Live-Ansicht
en:
  liveView: Live View
</i18n>
