export const sleep: (ms: number) => Promise<void> = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms))

export function promisify<T, A extends any[]>(
  func: (...args: [...A, (error: Error | null, result: T) => void]) => void,
): (...args: A) => Promise<T> {
  return function (...args: A): Promise<T> {
    return new Promise((resolve, reject) => {
      func(...args, (err: any, result: PromiseLike<T> | T) => {
        if (err) {
          reject(err)
        } else {
          resolve(result)
        }
      })
    })
  }
}
