export async function getJson(filename: string) {
    const res = await fetch(filename)
    const json = await res.json()

    return json
}