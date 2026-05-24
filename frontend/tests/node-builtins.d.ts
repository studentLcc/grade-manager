declare module 'node:fs' {
  export function readdirSync(path: string): string[]
  export function readFileSync(path: string, encoding: 'utf8'): string
  export function statSync(path: string): { isDirectory(): boolean }
}

declare module 'node:path' {
  export function dirname(path: string): string
  export function join(...paths: string[]): string
  export function relative(from: string, to: string): string
}

declare module 'node:url' {
  export function fileURLToPath(url: string | URL): string
}
