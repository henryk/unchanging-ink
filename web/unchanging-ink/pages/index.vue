<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="headline">
            {{ t('createOrVerify') }}
          </v-card-title>
          <v-tabs v-model="selectedTab" color="primary" grow>
            <v-tab value="create">{{ t('createTimestamp') }}</v-tab>
            <v-tab value="verify">{{ t('verifyTimestamp') }}</v-tab>
          </v-tabs>
          <v-window v-model="selectedTab">
            <v-window-item value="create">
              <v-card-text @dragover="doverHandler" @drop="dropHandler">
                <v-textarea
                  v-model="createInput.text"
                  :disabled="!!createInput.files.length"
                  :placeholder="textPlaceholder"
                />
                <v-file-input
                  v-model="createInput.files"
                  :placeholder="filesPlaceholder"
                  chips
                  multiple
                  counter
                  :disabled="!!createInput.text.length"
                />
                <v-expansion-panels v-model="extendedOptionsOpen">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ t('extendedOptions') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-select
                        v-model="createInput.hash"
                        :items="hashItems"
                        :label="t('hashfunction')"
                        item-title="text"
                        item-value="value"
                      />
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
              <v-expand-transition>
                <v-card-actions
                  v-show="createInput.text.length || createInput.files.length"
                >
                  <v-spacer></v-spacer>
                  <v-btn
                    size="large"
                    color="primary"
                    :disabled="
                      !createInput.text.length && !createInput.files.length
                    "
                    :loading="createLoading"
                    @click="doCreate"
                  >
                    <v-icon :icon="mdiStamper"></v-icon>
                    {{ t('createTimestamp') }}
<!--                    Fixme: Should do it dynamically based on progressToNext-->
                    <template #loader>
                      <v-progress-linear
                        color="primary"
                        height="10"
                        rounded
                        class="mx-2 flex-grow-1"
                        :indeterminate="createPending || progressToNext === null"
                        :model-value="
                          createPending || progressToNext === null
                            ? undefined
                            : progressToNext
                        "
                      />
                    </template>
                  </v-btn>
                </v-card-actions>
              </v-expand-transition>
            </v-window-item>
            <v-window-item value="verify">
              <v-card-text @dragover="doverHandler" @drop="dropHandler">
                <v-textarea
                  v-model="verifyInput.text"
                  :disabled="!!verifyInput.files.length"
                  :placeholder="textPlaceholder"
                />
                <v-file-input
                  v-model="verifyInput.files"
                  :placeholder="filesPlaceholder"
                  chips
                  multiple
                  counter
                  :disabled="!!verifyInput.text.length"
                />
                <v-textarea
                    v-model="verifyInput.ts"
                    placeholder="Timestamp / Proof JSON"
                  />
              </v-card-text>
              <v-expansion-panels v-model="extendedOptionsOpen">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    {{ t('extendedOptions') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select
                      v-model="verifyInput.hash"
                      :items="hashItems"
                      :label="t('hashfunction')"
                      item-title="text"
                      item-value="value"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
              <v-expand-transition>
                <v-card-actions
                  v-show="verifyInput.text.length || verifyInput.files.length"
                >
                  <v-spacer></v-spacer>
                  <v-btn
                    size="large"
                    color="primary"
                    :disabled="
                      (!verifyInput.text.length && !verifyInput.files.length) ||
                        !verifyInput.ts.length
                    "
                    @click="doVerify"
                  >
                    <v-icon :icon="mdiStamper"></v-icon>
                    {{ t('verifyTimestamp') }}
                  </v-btn>
                </v-card-actions>
              </v-expand-transition>
            </v-window-item>
          </v-window>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <timeline-card
          ref="timeline"
          :items="tickItems"
          :progress-to-next="progressToNext"
        />
      </v-col>
    </v-row>
    <v-row>
      <v-col v-if="createdTimestamps.length" cols="12" md="6">
        <v-card>
          <v-card-title class="headline">
            {{ t('createdTimestamps') }}
          </v-card-title>
          <v-card-text v-for="ts in createdTimestamps" :key="ts.id">
            <pre>{{ JSON.stringify(ts, null, 2) }}</pre>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-snackbar
      v-model="verifySnackbar.show"
      :color="verifySnackbar.color"
      :timeout="5000"
    >
      {{ verifySnackbar.message }}
      <template #action="{ attrs }">
        <v-btn variant="text" v-bind="attrs" @click="verifySnackbar.show = false">
          {{ t('close') }}
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>
<script setup>
import { mdiStamper } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import TimelineCard from '../components/Timeline'
import { computeHash } from '../utils/hashing'
import { sleep } from '../utils/misc'
import { TimestampService } from '../utils/uits'
import { validateTsInput } from '~/utils/validate'

const { t } = useI18n()
const runtimeConfig = useRuntimeConfig()

const UiTs = shallowRef(null)
const now = ref(new Date())
const nowInterval = ref(null)
const selectedTab = ref('create')
const extendedOptionsOpen = ref(false)
const createLoading = ref(false)
const createPending = ref(false)
const createdTimestamps = ref([])
const tickListener = ref(null)
const tickItems = ref([])
const createInput = reactive({
  text: '',
  files: [],
  hash: 'sha512',
})
const verifyInput = reactive({
  text: '',
  files: [],
  ts: '',
  hash: 'sha512',
})
const verifySnackbar = reactive({
  show: false,
  message: '',
  color: 'success',
})

const { data: initialTicks } = await useAsyncData(
  'recent-mth',
  async () => {
    if (!process.server) {
      return []
    }
    const { promisify } = await import('util')
    const redis = await import('redis')
    const serverService = new TimestampService(
      runtimeConfig.public.authority
    )
    const client = redis.createClient('redis://redis/0')
    const getAsync = promisify(client.get).bind(client)
    const val = await getAsync('recent-mth')
    client.quit?.()
    const recent = JSON.parse(val || '[]') ?? []
    recent.forEach((item) => serverService.tick(item, true))
    return JSON.parse(JSON.stringify(serverService.tickItems))
  }
)

if (initialTicks.value?.length) {
  tickItems.value = initialTicks.value
}

useHead(() => ({
  title: t('homepage'),
}))

const hashItems = computed(() => [
  { text: 'SHA-512', value: 'sha512' },
  { text: t('rawHash'), value: 'raw' },
])

const textPlaceholder = computed(() => {
  if (!createInput.files.length) {
    return t('dropTextOrDragFile')
  }
  return t('optionAddMoreFiles')
})

const filesPlaceholder = computed(() => {
  if (!createInput.text.length) {
    return t('alternateSelectFile')
  }
  return ''
})

const progressToNext = computed(() => {
  if (
    !UiTs.value?.estimatedNextTick ||
    !UiTs.value?.averageTickDurationMillis
  ) {
    return null
  }
  let diff =
    (UiTs.value.estimatedNextTick - now.value) /
    UiTs.value.averageTickDurationMillis
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
})

onMounted(() => {
  UiTs.value = new TimestampService(window.location.origin)
  if (tickItems.value?.length) {
    UiTs.value.tickItems = [...tickItems.value]
  }
  tickListener.value = UiTs.value.addListener((item) => {
    tickItems.value.unshift(item)
    tickItems.value = tickItems.value.slice(0, 5)
  })
  UiTs.value.openLiveConnection()
  nowInterval.value = window.setInterval(() => {
    now.value = new Date()
  }, 100)
})

onBeforeUnmount(() => {
  if (nowInterval.value !== null) {
    window.clearInterval(nowInterval.value)
    nowInterval.value = null
  }
  UiTs.value?.closeLiveConnection()
  if (tickListener.value !== null) {
    UiTs.value?.removeListener(tickListener.value)
    tickListener.value = null
  }
  UiTs.value = null
})

async function doCreate() {
  try {
    createLoading.value = true
    createPending.value = true

    const data_hash = await computeHash(createInput)
    const ts = await UiTs.value.getTimestamp(data_hash, {
      firstStepCallback: async () => {
        createPending.value = false
      },
    })
    await sleep(1000)
    console.log(await UiTs.value.verifyTimestamp(data_hash, ts))
    createdTimestamps.value.unshift(ts)
  } finally {
    createLoading.value = false
    createPending.value = false
  }
}

async function doVerify() {
  let verified = false
  let error = null
  try {
    const data_hash = await computeHash(verifyInput)
    const ts = await validateTsInput(JSON.parse(verifyInput.ts))
    verified = await UiTs.value.verifyTimestamp(data_hash, ts)
    console.log('Verified', verified)
  } catch (err) {
    error = err
  } finally {
    if (error) {
      verifySnackbar.show = true
      verifySnackbar.message = t('verifyError', { error: error.message })
      verifySnackbar.color = 'warning'
    } else if (verified) {
      verifySnackbar.show = true
      verifySnackbar.message = t('verifySuccess')
      verifySnackbar.color = 'success'
    } else {
      verifySnackbar.show = true
      verifySnackbar.message = t('verifyFailed')
      verifySnackbar.color = 'error'
    }
  }
}

function doverHandler(event) {
  event.preventDefault()
}

function dropHandler(event) {
  event.preventDefault()

  if (event.dataTransfer.items) {
    for (let i = 0; i < event.dataTransfer.items.length; i++) {
      if (event.dataTransfer.items[i].kind === 'file') {
        const file = event.dataTransfer.items[i].getAsFile()
        createInput.files.push(file)
      }
    }
  } else {
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
      createInput.files.push(event.dataTransfer.files[i])
    }
  }
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
  verifyError: 'Fehler bei der Überprüfung: {error}'
  verifySuccess: Zeitstempel ist für die bereitgestellten Daten gültig.
  verifyFailed: Zeitstempel ist NICHT gültig für die bereitgestellten Daten.
  close: Schließen
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
  verifyError: 'Error during verification: {error}'
  verifySuccess: Timestamp is valid for the provided data.
  verifyFailed: Timestamp is NOT valid for the provided data.
  close: Close
</i18n>
