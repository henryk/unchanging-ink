interface BaseInput {
  text: string
  files: File[]
}

export interface CreateInput extends BaseInput {
  hash: "sha512" | "raw"
}

export interface VerifyInput extends BaseInput {
  proof: string
}
