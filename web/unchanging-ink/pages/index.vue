<template>
  <v-container>
    <v-row class="mt-2">
      <v-col cols="6">
        <v-card>
          <v-tabs v-model="selectedTab" centered color="primary">
            <v-tab key="create">
              {{ $t("createTimestamp") }}
            </v-tab>
            <v-tab key="verify">
              {{ $t("verifyTimestamp") }}
            </v-tab>
          </v-tabs>
          <v-tabs-window
            v-model="selectedTab"
            @dragover="doverHandler"
            @drop="dropHandler"
          >
            <v-tabs-window-item key="create">
              <v-card-text>
                <v-textarea
                  v-model="createInput.text"
                  :disabled="!!createInput.files.length"
                  :placeholder="textPlaceholder"
                ></v-textarea>
                <v-file-input
                  v-model="createInput.files"
                  :disabled="!!createInput.text.length"
                  :placeholder="filesPlaceholder"
                  chips
                  counter
                  multiple
                ></v-file-input>
                <v-expansion-panels v-model="extendedOptionsOpen">
                  <v-expansion-panel :title="t('extendedOptions')">
                    <v-expansion-panel-text>
                      <v-select
                        v-model="createInput.hash"
                        :items="hashItems"
                        :label="t('hashfunction')"
                      ></v-select>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
              <v-expand-transition>
                <v-card-actions
                >
                  <v-spacer></v-spacer>
                  <v-btn
                    :disabled="
                      !createInput.text.length && !createInput.files.length
                    "
                    :loading="createLoading"
                    color="primary"
                    dark
                    large
                    @click="doCreate"
                  >
                    <v-icon dark>{{ mdiStamper }}</v-icon>
                    {{ $t("createTimestamp") }}
                    <template #loader>
                      <v-progress-linear
                        :indeterminate="createPending"
                        :query="true"
                        :value="createPending ? null : progressToNext"
                        class="mx-2"
                        color="white"
                        height="23"
                        striped
                      ></v-progress-linear>
                    </template>
                  </v-btn>
                </v-card-actions>
              </v-expand-transition>
            </v-tabs-window-item>

            <v-tabs-window-item key="verify">
              <v-card-text>
                <v-textarea
                  v-model="createInput.text"
                  :disabled="!!createInput.files.length"
                  :placeholder="textPlaceholder"
                ></v-textarea>
                <v-file-input
                  v-model="createInput.files"
                  :disabled="!!createInput.text.length"
                  :placeholder="filesPlaceholder"
                  chips
                  counter
                  multiple
                ></v-file-input>
              </v-card-text>
              <v-expand-transition>
                <v-card-actions
                  v-show="createInput.text.length || createInput.files.length"
                >
                  <v-text-field placeholder="proof"></v-text-field>
                  <v-spacer></v-spacer>
                  <v-btn
                    :disabled="
                      !createInput.text.length && !createInput.files.length
                    "
                    color="primary"
                    dark
                    large
                  >
                    <v-icon dark>{{ mdiStamper }}</v-icon>
                    {{ $t("verifyTimestamp") }}
                  </v-btn>
                </v-card-actions>
              </v-expand-transition>
            </v-tabs-window-item>
          </v-tabs-window>
        </v-card>
        <v-card>
          Ohai
        </v-card>
      </v-col>
      <v-col cols="6">
        <Timeline :items="ts.tickItems" :progress-to-next="progressToNext" />
      </v-col>
    </v-row>
  </v-container>
</template>
<script lang="ts" setup>
import type { CreateInput, VerifyInput } from "~/types"
import { mdiFileWord, mdiStamper } from "@mdi/js"

useHead({
  title: "Startseite",
})
const runtimeConfig = useRuntimeConfig()
const ts = useTimestampService(runtimeConfig.public.authority)
const now = useNow()
const { t } = useI18n()
const selectedTab = ref("create" as "create" | "verify")

const createInput = ref({ text: "", files: [], hash: "sha512" } as CreateInput)
const verifyInput = ref({ text: "", files: [], proof: "" } as VerifyInput)

const extendedOptionsOpen = ref(false)
const createLoading = ref(false)
const createPending = ref(false)
const createdTimestamps = ref([
  {
    mth: 'dev.unchanging.ink/63727#v1:APzuBvNkYzxDdj0VhPgfjwt7U_XfIEisAqWEOwu7za8',
    timestamp: 'dev.unchanging.ink/63727#v1,2024-06-24T17:43:31.510840Z,9DiYMeapMNSbkWSQJu_HEK0PFRU3bR-9jk1p1v_QAeA',
    filename: "Report.docx",
    icon: mdiFileWord
  }
] as any[])

const hashItems = [
  { title: "SHA-512", value: "sha512" },
  { title: t("rawHash"), value: "raw" },
] as { title: string; value: CreateInput["hash"] }[]

const progressToNext = computed(() => {
  if (!ts.value.estimatedNextTick || !ts.value.averageTickDurationMillis) {
    return
  }
  let diff =
    (ts.value.estimatedNextTick.getTime() - now.value.getTime()) /
    ts.value.averageTickDurationMillis
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

const textPlaceholder = computed(() => {
  if (!createInput.value.files.length) {
    return t("dropTextOrDragFile")
  } else {
    return t("optionAddMoreFiles")
  }
})

const filesPlaceholder = computed(() => {
  if (!createInput.value.text.length) {
    return t("alternateSelectFile")
  } else {
    return ""
  }
})

function doverHandler(event: Event) {
  event.preventDefault()
}

function dropHandler(event: DragEvent) {
  event.preventDefault()

  if (event.dataTransfer?.items) {
    // Use DataTransferItemList interface to access the file(s)
    for (let i = 0; i < event.dataTransfer.items.length; i++) {
      // If dropped items aren't files, reject them
      if (event.dataTransfer.items[i].kind === "file") {
        const file = event.dataTransfer.items[i].getAsFile()
        createInput.value.files.push(file!)
      }
    }
  } else if (event.dataTransfer?.files) {
    // Use DataTransfer interface to access the file(s)
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
      createInput.value.files.push(event.dataTransfer.files[i])
    }
  }
}

async function doCreate() {
  try {
    createLoading.value = true
    createPending.value = true
    const hash = await computeHash(createInput.value)
    const timestamp = await ts.value.getTimestamp(hash, {
      firstStepCallback: async () => {
        createPending.value = false
      },
    })
    await sleep(1000)
    console.log(await ts.value.verifyTimestamp(hash, timestamp))
    createdTimestamps.value.unshift(timestamp)
  } finally {
    createLoading.value = false
    createPending.value = false
  }
}
</script>
