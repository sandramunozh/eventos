import { FormEvent, useState } from 'react'
import { Search, BadgeCheck, XCircle } from 'lucide-react'

type TerceroData = {
  cuCod: number
  cuNumId: string
  cuPriNom: string
  cuSegNom: string | null
  cuPriApe: string
  cuSegApe: string | null
  identificacion: string
  tercero: string
  nomTercero: string
}

type LookupResult = { result: number; message: string; data: TerceroData | null }

export default function CuentasPage({ api }: {
  api: (path: string, init?: RequestInit) => Promise<unknown>
}) {
  const [ident, setIdent] = useState('')
  const [lookup, setLookup] = useState<LookupResult | null>(null)
  const [lookupLoading, setLookupLoading] = useState(false)
  const [error, setError] = useState('')

  async function consultarTercero(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const num = ident.trim()
    if (!num) {
      setLookup({ result: -2, message: 'El número de identificación es requerido.', data: null })
      return
    }
    setLookupLoading(true); setLookup(null); setError('')
    try {
      const res = await api(`/cuentas/tercero/${encodeURIComponent(num)}`) as LookupResult
      setLookup(res)
      if (res.result === 1) setIdent('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible consultar el tercero')
    } finally { setLookupLoading(false) }
  }

  return <>
    <div className="page-heading">
      <div>
        <p className="eyebrow">GESTIÓN COMERCIAL</p>
        <h1>Cuentas</h1>
        <p className="muted">Consulta los datos del tercero por número de identificación (MUF y JDE).</p>
      </div>
    </div>

    {error && <p className="error" role="alert">{error}</p>}

    <section className="panel">
      <h2>Consultar tercero por identificación</h2>
      <p className="muted">Ingresa el número sin separadores de miles (ej.: 75084840).</p>
      <form className="lookup-form" onSubmit={consultarTercero}>
        <input
          value={ident}
          onChange={(e) => setIdent(e.target.value)}
          placeholder="Número de identificación"
          aria-label="Número de identificación"
          minLength={4}
          maxLength={20}
        />
        <button className="primary" type="submit" disabled={lookupLoading}>
          <Search size={16}/>{lookupLoading ? 'Consultando…' : 'Consultar'}
        </button>
      </form>
      {lookup && (
        lookup.result === 1 && lookup.data ? (
          <div className="lookup-result">
            <div className="lookup-field"><small>Cód. cuenta MUF (cuCod)</small><strong>{lookup.data.cuCod}</strong></div>
            <div className="lookup-field"><small>Identificación del titular (cuNumId)</small><strong>{lookup.data.cuNumId}</strong></div>
            <div className="lookup-field"><small>Primer nombre (cuPriNom)</small><strong>{lookup.data.cuPriNom || '—'}</strong></div>
            <div className="lookup-field"><small>Segundo nombre (cuSegNom)</small><strong>{lookup.data.cuSegNom || '—'}</strong></div>
            <div className="lookup-field"><small>Primer apellido (cuPriApe)</small><strong>{lookup.data.cuPriApe || '—'}</strong></div>
            <div className="lookup-field"><small>Segundo apellido (cuSegApe)</small><strong>{lookup.data.cuSegApe || '—'}</strong></div>
            <div className="lookup-field"><small>Identificación en JDE (identificacion)</small><strong>{lookup.data.identificacion || '—'}</strong></div>
            <div className="lookup-field"><small>Tercero JDE / ABAN8 (tercero)</small><strong>{lookup.data.tercero || '—'}</strong></div>
            <div className="lookup-field"><small>Nombre tercero JDE / ABALPH (nomTercero)</small><strong>{lookup.data.nomTercero || '—'}</strong></div>
            <div className="lookup-field ok"><BadgeCheck size={16}/> <span>{lookup.message}</span></div>
          </div>
        ) : (
          <p className="lookup-vacio"><XCircle size={16}/> {lookup.message || 'Sin datos.'}</p>
        )
      )}
    </section>
    <p className="fine-print">Los datos provienen del servicio WebApiComfamiliar (api/Facturacion/Tercero). Los campos JDE se muestran vacíos cuando no hay coincidencia.</p>
  </>
}
