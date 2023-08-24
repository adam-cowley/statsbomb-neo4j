import { HOSTNAME } from "../config"


const SB_USERNAME = 'liammccartan7@gmail.com'
const SB_PASSWORD = 'BUOfCRC3'

export async function getJson(filename: string) {
    const headers = new Headers()
    if (filename.includes(HOSTNAME)) {
        headers.set('authorization', 'Basic ' + Buffer.from(SB_USERNAME + ":" + SB_PASSWORD).toString('base64'))
    }

    const res = await fetch(filename, { headers })
    const json = await res.json()

    return json
}