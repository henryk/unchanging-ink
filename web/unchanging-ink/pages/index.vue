<template>
  <v-row>
    <v-col cols="12" md="6">
      <v-card>
        <v-card-title class="headline">{{ $t('createOrVerify') }}</v-card-title>
        <v-tabs v-model="selectedTab" color="primary" grow>
          <v-tab key="create">{{ $t('createTimestamp') }}</v-tab>
          <v-tab key="verify">{{ $t('verifyTimestamp') }}</v-tab>
        </v-tabs>
        <v-tabs-items v-model="selectedTab" color="primary">
          <v-tab-item key="create">
            <v-card-text @dragover="doverHandler" @drop="dropHandler">
              <v-textarea
                v-model="createInput.text"
                :disabled="!!createInput.files.length"
                :placeholder="textPlaceholder"
              ></v-textarea>
              <v-file-input
                v-model="createInput.files"
                :placeholder="filesPlaceholder"
                chips
                multiple
                counter
                :disabled="!!createInput.text.length"
              ></v-file-input>
            </v-card-text>
            <v-card-actions
              ><v-spacer></v-spacer
              ><v-btn
                large
                dark
                color="primary"
                :disabled="
                  !createInput.text.length && !createInput.files.length
                "
                ><v-icon dark>mdi-stamper</v-icon>
                {{ $t('createTimestamp') }}</v-btn
              ></v-card-actions
            >
          </v-tab-item>
          <v-tab-item key="verify">
            <v-card-text @dragover="doverHandler" @drop="dropHandler">
              <v-textarea
                v-model="createInput.text"
                :disabled="!!createInput.files.length"
                :placeholder="textPlaceholder"
              ></v-textarea>
              <v-file-input
                v-model="createInput.files"
                :placeholder="filesPlaceholder"
                chips
                multiple
                counter
                :disabled="!!createInput.text.length"
              ></v-file-input>
            </v-card-text>
            <v-card-actions
              ><v-text-field placeholder="proof"></v-text-field
              ><v-spacer></v-spacer
              ><v-btn
                large
                dark
                color="primary"
                :disabled="
                  !createInput.text.length && !createInput.files.length
                "
                ><v-icon dark>mdi-stamper</v-icon>
                {{ $t('verifyTimestamp') }}</v-btn
              ></v-card-actions
            >
          </v-tab-item>
        </v-tabs-items>
      </v-card>
    </v-col>
    <v-col cols="12" md="6">
      <v-card @mouseenter="pauseMover = true" @mouseleave="pauseMover = false">
        <v-card-title class="headline">
          {{ $t('liveView') }}
          <v-spacer></v-spacer>
          <v-icon v-if="paused">mdi-pause</v-icon
          ><v-icon v-else>mdi-play</v-icon>
        </v-card-title>
        <v-card-text style="max-height: 35em; overflow-y: hidden">
          <v-timeline v-show="items.length" clipped dense>
            <transition-group name="slide-y-transition">
              <v-timeline-item
                v-for="item in items"
                :key="item.time"
                fill-dot
                color="primary"
                right
              >
                <v-card>
                  <v-card-subtitle
                    >{{ item.time }}
                    <v-icon color="success">mdi-check</v-icon></v-card-subtitle
                  >
                  <v-card-text style="font-family: Roboto Mono, monospace">{{
                    item.hash
                  }}</v-card-text>
                </v-card>
                <template #icon>
                  <v-avatar
                    ><span
                      class="white--text"
                      style="
                        font-family: Roboto Mono, monospace;
                        line-height: 0.9;
                        white-space: pre-line;
                      "
                      >{{ item.icon }}</span
                    ></v-avatar
                  ></template
                >
              </v-timeline-item>
            </transition-group>
          </v-timeline>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
const HEX_CHARS = '0123456789ABCDEF'

export default {
  data() {
    return {
      selectedTab: 'create',
      rawItems: [],
      pausedItems: [],
      pauseMover: false,
      pauseBackground: false,
      cbHandle: null,
      createInput: {
        text: '',
        files: [],
      },
      verifyInput: {
        text: '',
        files: [],
        proof: '',
      },
    }
  },
  // eslint-disable-next-line require-await
  async fetch() {
    this.tick({
      timestamp: new Date().toLocaleString(),
      hash: [...Array(64)]
        .map((_) =>
          HEX_CHARS.charAt(Math.floor(Math.random() * HEX_CHARS.length))
        )
        .join(''),
    })
  },
  computed: {
    items() {
      return this.paused ? this.pausedItems : this.rawItems
    },
    paused() {
      return this.pauseMover || this.pauseBackground
    },
    textPlaceholder() {
      if (!this.createInput.files.length) {
        return this.$t('dropTextOrDragFile')
      } else {
        return this.$t('optionAddMoreFiles')
      }
    },
    filesPlaceholder() {
      if (!this.createInput.text.length) {
        return this.$t('alternateSelectFile')
      } else {
        return ''
      }
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
    this.$options.sockets.onmessage = this.receiveMessage
    document.addEventListener(
      'visibilitychange',
      this.handleVisibilityChange,
      false
    )
  },
  beforeDestroy() {
    if (this.cbHandle) {
      window.clearInterval(this.cbHandle)
      this.cbHandle = null
    }
    delete this.$options.sockets.onmessage
  },
  methods: {
    receiveMessage(event) {
      const data = JSON.parse(event?.data ?? '')
      this.tick(data)
    },
    handleVisibilityChange() {
      this.pauseBackground = document.hidden
    },
    tick(data) {
      const item = {
        time: data?.timestamp ?? 'not set',
        hash: data?.hash ?? 'NOT SET',
        icon: [...Array(3)]
          .map((_) =>
            [...Array(5)]
              .map((_) =>
                HEX_CHARS.charAt(Math.floor(Math.random() * HEX_CHARS.length))
              )
              .join('')
          )
          .join('\n'),
      }
      this.rawItems.unshift(item)
      if (this.rawItems.length > 5) {
        this.rawItems.pop()
      }
      return true
    },
    doverHandler(event) {
      event.preventDefault()
    },
    dropHandler(event) {
      event.preventDefault()

      if (event.dataTransfer.items) {
        // Use DataTransferItemList interface to access the file(s)
        for (let i = 0; i < event.dataTransfer.items.length; i++) {
          // If dropped items aren't files, reject them
          if (event.dataTransfer.items[i].kind === 'file') {
            const file = event.dataTransfer.items[i].getAsFile()
            this.createInput.files.push(file)
          }
        }
      } else {
        // Use DataTransfer interface to access the file(s)
        for (let i = 0; i < event.dataTransfer.files.length; i++) {
          this.createInput.files.push(event.dataTransfer.files[i])
        }
      }
    },
  },
}
</script>
<i18n lang="yaml">
de:
  createTimestamp: Zeitstempel erzeugen
  verifyTimestamp: Zeitstempel überprüfen
  createOrVerify: Erzeugen oder Überprüfen
  dropTextOrDragFile: Hier Text eintragen oder Datei ziehen
  optionAddMoreFiles: 'Optional: Mehr Dateien hinzufügen'
  alternateSelectFile: 'Alternativ: Datei wählen'
en:
  createTimestamp: Create timestamp
  verifyTimestamp: Verify timestamp
  createOrVerify: Create or Verify
  dropTextOrDragFile: Enter text or drag and drop file here
  optionAddMoreFiles: 'Optional: Add more files'
  alternateSelectFile: 'Alternatively: Select file'
</i18n>
