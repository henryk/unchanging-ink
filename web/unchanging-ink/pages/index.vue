<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="headline">{{
            $t('createOrVerify')
          }}</v-card-title>
          <v-tabs v-model="selectedTab" color="primary" grow>
            <v-tab key="create">{{ $t('createTimestamp') }}</v-tab>
            <v-tab key="verify" disabled>{{ $t('verifyTimestamp') }}</v-tab>
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
                <v-expansion-panels v-model="extendedOptionsOpen">
                  <v-expansion-panel>
                    <v-expansion-panel-header>{{
                      $t('extendedOptions')
                    }}</v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <v-select
                        v-model="createInput.hash"
                        :items="hashItems"
                        :label="$t('hashfunction')"
                      ></v-select>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
              <v-expand-transition
                ><v-card-actions
                  v-show="createInput.text.length || createInput.files.length"
                  ><v-spacer></v-spacer
                  ><v-btn
                    large
                    dark
                    color="primary"
                    :disabled="
                      !createInput.text.length && !createInput.files.length
                    "
                    :loading="createLoading"
                    @click="doCreate"
                    ><v-icon dark>{{ mdiStamper }}</v-icon>
                    {{ $t('createTimestamp') }}
                    <template #loader>
                      <v-progress-linear
                        color="white"
                        height="23"
                        striped
                        class="mx-2"
                        :query="true"
                        :indeterminate="createPending"
                        :value="createPending ? null : progressToNext"
                      ></v-progress-linear>
                    </template> </v-btn></v-card-actions
              ></v-expand-transition>
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
              <v-expand-transition
                ><v-card-actions
                  v-show="createInput.text.length || createInput.files.length"
                  ><v-text-field placeholder="proof"></v-text-field
                  ><v-spacer></v-spacer
                  ><v-btn
                    large
                    dark
                    color="primary"
                    :disabled="
                      !createInput.text.length && !createInput.files.length
                    "
                    ><v-icon dark>{{ mdiStamper }}</v-icon>
                    {{ $t('verifyTimestamp') }}</v-btn
                  ></v-card-actions
                ></v-expand-transition
              >
            </v-tab-item>
          </v-tabs-items>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <timeline-card
          ref="timeline"
          :items="tickItems"
          :progress-to-next="progressToNext"
        ></timeline-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col v-if="createdTimestamps.length" cols="12" md="6">
        <v-card>
          <v-card-title class="headline">{{
            $t('createdTimestamps')
          }}</v-card-title>
          <v-card-text v-for="ts in createdTimestamps" :key="ts.id">
            <pre>{{ JSON.stringify(ts, null, 2) }}</pre>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import { mdiStamper } from '@mdi/js'
import redis from 'redis'
import { computeHash } from '~/utils/hashing'
import TimelineCard from '../components/Timeline'
import { TimestampService } from '~/utils/uits'
import { promisify, sleep } from '~/utils/misc'

export default {
  components: {
    TimelineCard,
  },
  asyncData() {
    return {
      UiTs: new TimestampService(process.env.AUTHORITY),
    }
  },
  data() {
    return {
      mdiStamper,
      now: new Date(),
      nowInterval: null,
      selectedTab: 'create',
      extendedOptionsOpen: false,
      createLoading: false,
      createPending: false,
      createdTimestamps: [],
      UiTs: null,
      tickListener: null,
      tickItems: [],
      createInput: {
        text: '',
        files: [],
        hash: 'sha512',
      },
      verifyInput: {
        text: '',
        files: [],
        proof: '',
      },
    }
  },
  async fetch() {
    if (process.server) {
      const client = redis.createClient('redis://redis/0')
      const getAsync = promisify(client.get).bind(client)
      const val = await getAsync('recent-mth')
      const recent = JSON.parse(val)
      ;(recent ?? []).forEach((item) => this.UiTs.tick(item, true))
      this.tickItems = JSON.parse(JSON.stringify(this.UiTs.tickItems))
    }
  },
  head() {
    return {
      title: this.$t('homepage'),
    }
  },
  computed: {
    hashItems() {
      return [
        { text: 'SHA-512', value: 'sha512' },
        { text: this.$t('rawHash'), value: 'raw' },
      ]
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
    progressToNext() {
      if (
        !this.UiTs.estimatedNextTick ||
        !this.UiTs.averageTickDurationMillis
      ) {
        return null
      }
      let diff =
        (this.UiTs.estimatedNextTick - this.now) /
        this.UiTs.averageTickDurationMillis
      if (diff < 0) {
        diff = 0
      }
      if (diff > 1.0) {
        diff = 1.0
      }
      diff = (1.0 - diff) * 100
      diff = (100.0 / 80.0) * diff - (20 * 100) / 80
      if (diff < 0) {
        diff = 0
      }
      return diff
    },
  },
  mounted() {
    this.UiTs = new TimestampService(window.location.origin) // Client side
    this.tickListener = this.UiTs.addListener((item) => {
      this.tickItems.unshift(item)
      this.$forceUpdate()
    })
    this.UiTs.openLiveConnection()
    this.nowInterval = window.setInterval(this.nowHandler, 100)
  },
  beforeDestroy() {
    if (this.nowInterval !== null) {
      window.clearInterval(this.nowInterval)
      this.nowInterval = null
    }
    this.UiTs.closeLiveConnection()
    if (this.tickListener !== null) {
      this.UiTs.removeListener(this.tickListener)
      this.tickListener = null
    }
    delete this.UiTs
  },
  methods: {
    nowHandler() {
      this.now = new Date()
    },
    async doCreate() {
      try {
        this.createLoading = true
        this.createPending = true
        const hash = await computeHash(this.createInput)
        const ts = await this.UiTs.getTimestamp(hash, {
          // eslint-disable-next-line require-await
          firstStepCallback: async () => {
            this.createPending = false
          },
        })
        await sleep(1000)
        console.log(await this.UiTs.verifyTimestamp(hash, ts))
        this.createdTimestamps.unshift(ts)
      } finally {
        this.createLoading = false
        this.createPending = false
      }
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
  homepage: Startseite
  dropTextOrDragFile: Hier Text eintragen oder Datei ziehen
  optionAddMoreFiles: 'Optional: Mehr Dateien hinzufügen'
  alternateSelectFile: 'Alternativ: Datei wählen'
  hashfunction: Hash-Funktion
  extendedOptions: Erweiterte Einstellungen
  rawHash: Rohdaten/ungehasht (max 256 Bytes)
  createdTimestamps: Zuletzt erzeugte Zeitstempel
en:
  createTimestamp: Create timestamp
  verifyTimestamp: Verify timestamp
  createOrVerify: Create or Verify
  homepage: Home Page
  dropTextOrDragFile: Enter text or drag and drop file here
  optionAddMoreFiles: 'Optional: Add more files'
  alternateSelectFile: 'Alternatively: Select file'
  hashfunction: Hash function
  extendedOptions: Extended Options
  rawHash: raw/no hash (max 256 bytes)
  createdTimestamps: Created timestamps
</i18n>
