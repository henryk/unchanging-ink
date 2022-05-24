<template>
  <v-card
    :loading="true"
    @mouseenter="pauseMover = true"
    @mouseleave="pauseMover = false"
  >
    <template #progress>
      <v-progress-linear
        :value="!paused ? progressToNext : null"
      ></v-progress-linear>
    </template>
    <v-card-title class="headline">
      {{ $t('liveView') }}
      <v-spacer></v-spacer>
      <v-icon v-if="paused">{{ mdiPause }}</v-icon
      ><v-icon v-else>{{ mdiPlay }}</v-icon>
    </v-card-title>
    <v-card-text style="max-height: 35em; overflow-y: hidden">
      <v-timeline v-show="items.length" clipped dense>
        <transition-group name="slide-y-transition">
          <timeline-item-card
            v-for="item in items"
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
  },
  data() {
    return {
      mdiPause,
      mdiPlay,
      rawItems: [],
      pausedItems: [],
      pauseMover: false,
      pauseBackground: false,
    }
  },
  computed: {
    items() {
      return this.paused ? this.pausedItems : this.rawItems
    },
    paused() {
      return this.pauseMover || this.pauseBackground
    },
  },
  watch: {
    paused(newVal) {
      if (newVal) {
        this.pausedItems = [...this.rawItems]
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
    tick(item) {
      this.rawItems.unshift(item)
      if (this.rawItems.length > 5) {
        this.rawItems.pop()
      }
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
