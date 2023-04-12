interface CreateInput {
  text: string;
  files: File[];
  hash: "sha512" | "raw";
}
