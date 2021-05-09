<template>
  <v-row justify="center" align="center">
    <v-col cols="12" sm="8" md="6">
      <v-card>
        <v-card-title class="headline">
          {{ $t('welcome') }}
        </v-card-title>
        <v-card-text>
          <transition-group name="fade" tag="ul">
            <li v-for="(item, index) in items" :key="index">
              {{ item }}
            </li>
          </transition-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
export default {
  data() {
    return {
      items: [],
      cbHandle: null,
    }
  },
  mounted() {
    this.cbHandle = window.setInterval(() => {
      return this.tick()
    }, 3000)
  },
  beforeDestroy() {
    if (this.cbHandle) {
      window.clearInterval(this.cbHandle)
      this.cbHandle = null
    }
  },
  methods: {
    tick() {
      this.items.push(new Date().toISOString())
      if (this.items.length > 5) {
        this.items.shift()
      }
      return true
    },
  },
}
</script>
