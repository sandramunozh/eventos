import { FormEvent, useEffect, useState } from 'react'
import { ArrowLeft, CalendarDays, ChevronLeft, ChevronRight, Clock, Mail, MapPin, Phone, PlusCircle, UserRound } from 'lucide-react'

type Actividad = {
  id: number; tarea: string; estado: string; fecha: string; hora: string | null
  lugar_empresa?: string | null; empresa_nit?: string | null; empresa_nombre?: string | null
  contacto?: string | null; correo_contacto?: string | null; telefono?: string | null
  descripcion?: string | null
}

type Vista = 'anio' | 'mes' | 'semana' | 'dia'

const TAREAS = ['LLAMADA TELEFÓNICA', 'VISITA', 'FERIA DE SERVICIOS', 'STAND INFORMATIVO', 'ACOMPAÑAMIENTO EVENTO', 'CHARLA DE SERVICIOS', 'MODELO (RELACIONAMIENTO)', 'VISITA VIRTUAL', 'CHARLA DE SERVICIOS VIRTUAL', 'ACOMPAÑAR. EVENTO VIRTUAL']
const ESTADOS = ['NO INICIADA', 'REALIZADA', 'CANCELADA', 'NO EFECTIVA', 'CREADA ERROR']

const NOMBRES_MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
const DIAS_CORTOS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
const DIAS_LARGOS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

const HOY = new Date()

function aISO(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function deISO(iso: string): Date {
  const [a, m, d] = iso.split('-').map(Number)
  return new Date(a, m - 1, d)
}

function inicioSemana(d: Date): Date {
  const copia = new Date(d)
  copia.setDate(copia.getDate() - ((copia.getDay() + 6) % 7))
  return copia
}

function sumarDias(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
}

function fechasMesGrid(ref: Date): string[] {
  const primero = new Date(ref.getFullYear(), ref.getMonth(), 1)
  const inicio = sumarDias(primero, -((primero.getDay() + 6) % 7))
  return Array.from({ length: 42 }, (_, i) => aISO(sumarDias(inicio, i)))
}

function fechasSemana(ref: Date): string[] {
  const inicio = inicioSemana(ref)
  return Array.from({ length: 7 }, (_, i) => aISO(sumarDias(inicio, i)))
}

function claseEstado(estado: string): string {
  if (estado === 'REALIZADA') return ''
  if (estado === 'CANCELADA') return 'badge-alerta'
  if (estado === 'NO EFECTIVA') return 'badge-aviso'
  if (estado === 'CREADA ERROR') return 'badge-error'
  return 'badge-vacio'
}

function claseChip(estado: string): string {
  if (estado === 'CANCELADA') return 'cal-chip cancelada'
  if (estado === 'NO EFECTIVA') return 'cal-chip noefectiva'
  if (estado === 'REALIZADA') return 'cal-chip'
  if (estado === 'CREADA ERROR') return 'cal-chip creada-error'
  return 'cal-chip no-iniciada'
}

function horaCorta(hora: string | null): string {
  return hora ? hora.slice(0, 5) : ''
}

function fechaLarga(iso: string): string {
  const d = deISO(iso)
  return `${DIAS_LARGOS[(d.getDay() + 6) % 7]} ${d.getDate()} de ${NOMBRES_MES[d.getMonth()]} de ${d.getFullYear()}`
}

function TarjetaActividad({ act, onEstado }: { act: Actividad; onEstado: (id: number, estado: string) => void }) {
  return <article className="agenda-card">
    <div className="request-top">
      <strong className="agenda-tarea">{act.tarea}</strong>
      <span className={`badge ${claseEstado(act.estado)}`}>{act.estado}</span>
    </div>
    <div className="agenda-meta">
      {act.hora && <span><Clock size={14}/>{horaCorta(act.hora)}</span>}
      {(act.lugar_empresa || act.empresa_nombre) && <span><MapPin size={14}/>{act.lugar_empresa || act.empresa_nombre}</span>}
      {act.contacto && <span><UserRound size={14}/>{act.contacto}</span>}
      {act.correo_contacto && <span><Mail size={14}/>{act.correo_contacto}</span>}
      {act.telefono && <span><Phone size={14}/>{act.telefono}</span>}
    </div>
    {act.empresa_nit && <p className="agenda-empresa">NIT: {act.empresa_nit}{act.empresa_nombre ? ` · ${act.empresa_nombre}` : ''}</p>}
    {act.descripcion && <p className="agenda-desc">{act.descripcion}</p>}
    <div className="agenda-accion">
      <label>Cambiar estado
        <select value={act.estado} onChange={(e) => onEstado(act.id, e.target.value)}>
          {ESTADOS.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
      </label>
    </div>
  </article>
}

export default function AgendaPage({ api }: {
  api: (path: string, init?: RequestInit) => Promise<unknown>
}) {
  const [vista, setVista] = useState<Vista>('mes')
  const [referencia, setReferencia] = useState<Date>(HOY)
  const [diaSeleccionado, setDiaSeleccionado] = useState<string | null>(null)
  const [actividades, setActividades] = useState<Actividad[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  const [mostrarForm, setMostrarForm] = useState(false)

  const porDia = new Map<string, Actividad[]>()
  for (const act of actividades) {
    const clave = act.fecha.slice(0, 10)
    porDia.set(clave, [...(porDia.get(clave) || []), act])
  }

  async function cargar() {
    setLoading(true); setError('')
    try {
      let desde: string, hasta: string
      if (diaSeleccionado) {
        desde = hasta = diaSeleccionado
      } else if (vista === 'anio') {
        desde = `${referencia.getFullYear()}-01-01`; hasta = `${referencia.getFullYear()}-12-31`
      } else if (vista === 'mes') {
        const grid = fechasMesGrid(referencia); desde = grid[0]; hasta = grid[grid.length - 1]
      } else if (vista === 'semana') {
        const sem = fechasSemana(referencia); desde = sem[0]; hasta = sem[6]
      } else {
        desde = hasta = aISO(referencia)
      }
      const res = await api(`/agenda?desde=${desde}&hasta=${hasta}`) as Actividad[]
      setActividades(Array.isArray(res) ? res : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de conexión')
    } finally { setLoading(false) }
  }

  useEffect(() => { void cargar() }, [vista, referencia, diaSeleccionado, version])

  function refrescar() { setVersion((v) => v + 1) }

  function navegar(direccion: number) {
    if (vista === 'anio') setReferencia(new Date(referencia.getFullYear() + direccion, 0, 1))
    else if (vista === 'mes') setReferencia(new Date(referencia.getFullYear(), referencia.getMonth() + direccion, 1))
    else if (vista === 'semana') setReferencia(sumarDias(referencia, 7 * direccion))
    else setReferencia(sumarDias(referencia, direccion))
  }

  function tituloVista(): string {
    if (vista === 'anio') return String(referencia.getFullYear())
    if (vista === 'mes') {
      const n = NOMBRES_MES[referencia.getMonth()]
      return `${n.charAt(0).toUpperCase()}${n.slice(1)} ${referencia.getFullYear()}`
    }
    if (vista === 'semana') {
      const sem = fechasSemana(referencia)
      return `Semana del ${deISO(sem[0]).getDate()} al ${deISO(sem[6]).getDate()} de ${NOMBRES_MES[deISO(sem[6]).getMonth()]}`
    }
    return fechaLarga(aISO(referencia)).replace(/^./, (c) => c.toUpperCase())
  }

  async function cambiarEstado(id: number, estado: string) {
    try {
      await api(`/agenda/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ estado }) })
      refrescar()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible actualizar el estado')
    }
  }

  async function guardarActividad(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const data = new FormData(form)
    const valor = (k: string) => String(data.get(k) || '').trim()
    const hora = valor('hora')
    const correo = valor('correo_contacto')
    try {
      await api('/agenda', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tarea: valor('tarea'),
          estado: valor('estado') || 'NO INICIADA',
          fecha: valor('fecha'),
          hora: hora || null,
          lugar_empresa: valor('lugar_empresa') || null,
          empresa_nit: valor('empresa_nit') || null,
          empresa_nombre: valor('empresa_nombre') || null,
          contacto: valor('contacto') || null,
          correo_contacto: correo || null,
          telefono: valor('telefono') || null,
          descripcion: valor('descripcion') || null,
        }),
      })
      setMostrarForm(false); form.reset(); refrescar()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible guardar la actividad')
    }
  }

  const chips = (iso: string) => porDia.get(iso) || []

  return <>
    <div className="page-heading">
      <div>
        <p className="eyebrow">AGENDA</p>
        <h1>Agenda del día</h1>
        <p className="muted">Calendario de actividades comerciales: filtra por año, mes, semana o día.</p>
      </div>
    </div>

    {error && <p className="error" role="alert">{error}</p>}

    {diaSeleccionado ? (
      <>
        <div className="panel">
          <div className="panel-heading">
            <div>
              <h2>Agenda del {fechaLarga(diaSeleccionado)}</h2>
              <p className="muted">{chips(diaSeleccionado).length} actividad(es) programada(s){loading ? ' · actualizando…' : ''}</p>
            </div>
            <div className="filter-actions">
              <button className="secondary" onClick={() => setDiaSeleccionado(null)}><ArrowLeft size={16}/>Volver al calendario</button>
              <button className="primary" onClick={() => setMostrarForm(!mostrarForm)}><PlusCircle size={16}/>{mostrarForm ? 'Cerrar formulario' : 'Nueva actividad'}</button>
            </div>
          </div>

          {mostrarForm && (
            <form className="form-grid" onSubmit={guardarActividad}>
              <label>Tarea*
                <select name="tarea" required defaultValue="VISITA">
                  {TAREAS.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </label>
              <label>Estado
                <select name="estado" defaultValue="NO INICIADA">
                  {ESTADOS.map((e2) => <option key={e2} value={e2}>{e2}</option>)}
                </select>
              </label>
              <label>Fecha programada*
                <input type="date" name="fecha" required defaultValue={diaSeleccionado} />
              </label>
              <label>Hora
                <input type="time" name="hora" />
              </label>
              <label>Lugar de la actividad (Empresa)
                <input name="lugar_empresa" maxLength={180} placeholder="Nombre del lugar" />
              </label>
              <label>NIT o Nombre de la empresa
                <input name="empresa_nit" maxLength={40} placeholder="NIT de la empresa" />
              </label>
              <label>Empresa (nombre comercial / razón social)
                <input name="empresa_nombre" maxLength={180} />
              </label>
              <label>Contacto
                <input name="contacto" maxLength={160} />
              </label>
              <label>Correo contacto
                <input type="email" name="correo_contacto" maxLength={254} />
              </label>
              <label>Teléfono
                <input name="telefono" maxLength={20} minLength={6} />
              </label>
              <label className="full">Resumen de la reunión o descripción de las actividades
                <textarea name="descripcion" rows={5} maxLength={20000} />
              </label>
              <div className="full form-actions">
                <button type="button" className="secondary" onClick={() => setMostrarForm(false)}>Cancelar</button>
                <button type="submit" className="primary">Guardar actividad</button>
              </div>
            </form>
          )}

          {chips(diaSeleccionado).length === 0 && !mostrarForm && (
            <div className="empty"><CalendarDays size={28}/><strong>Sin actividades para este día</strong><span>Use "Nueva actividad" para programar una.</span></div>
          )}

          {chips(diaSeleccionado).length > 0 && (
            <div className="agenda-cards">
              {chips(diaSeleccionado).map((act) => <TarjetaActividad key={act.id} act={act} onEstado={cambiarEstado}/>)}
            </div>
          )}
        </div>
      </>
    ) : (
      <section className="panel">
        <div className="cal-toolbar">
          <div className="cal-nav">
            <button className="icon-button" onClick={() => navegar(-1)} aria-label="Anterior"><ChevronLeft size={18}/></button>
            <button className="icon-button" onClick={() => navegar(1)} aria-label="Siguiente"><ChevronRight size={18}/></button>
            <button className="secondary" onClick={() => { setReferencia(new Date()); refrescar() }}>Fecha actual</button>
          </div>
          <span className="cal-titulo">{tituloVista()}</span>
          <div className="cal-vistas">
            {([['anio', 'Año'], ['mes', 'Mes'], ['semana', 'Semana'], ['dia', 'Día']] as [Vista, string][]).map(([v, etiqueta]) => (
              <button key={v} className={vista === v ? 'activo' : ''} onClick={() => setVista(v)}>{etiqueta}</button>
            ))}
          </div>
        </div>

        {vista === 'anio' && (
          <div className="anio-grid">
            {Array.from({ length: 12 }, (_, m) => {
              const anio = referencia.getFullYear()
              const primero = new Date(anio, m, 1)
              const inicio = sumarDias(primero, -((primero.getDay() + 6) % 7))
              const dias = new Date(anio, m + 1, 0).getDate()
              return <div key={m} className="mini-mes" onClick={() => { setReferencia(new Date(anio, m, 1)); setVista('mes') }}>
                <h3>{NOMBRES_MES[m].replace(/^./, (c) => c.toUpperCase())}</h3>
                <div className="mini-grid">
                  {DIAS_CORTOS.map((d) => <span key={d} className="mini-num mini-enc">{d.charAt(0)}</span>)}
                  {Array.from({ length: (inicio.getDay() + 6) % 7 }, (_, i) => <span key={`p${i}`} className="mini-num"/>)}
                  {Array.from({ length: dias }, (_, i) => {
                    const iso = aISO(new Date(anio, m, i + 1))
                    const tiene = chips(iso).length > 0
                    return <span key={iso} className={`mini-num ${aISO(HOY) === iso ? 'hoy' : ''} ${tiene ? 'con-actividades' : ''}`}>{i + 1}</span>
                  })}
                </div>
              </div>
            })}
          </div>
        )}

        {vista === 'mes' && (
          <div className="cal-wrap">
            <div className="cal-grid mes">
              {DIAS_CORTOS.map((d) => <div key={d} className="cal-enc">{d}</div>)}
              {fechasMesGrid(referencia).map((iso) => {
                const d = deISO(iso)
                const otroMes = d.getMonth() !== referencia.getMonth()
                const acts = chips(iso)
                return <div key={iso} className={`cal-celda ${otroMes ? 'otro' : ''} ${aISO(HOY) === iso ? 'hoy' : ''}`} onClick={() => setDiaSeleccionado(iso)}>
                  <span className="cal-num">{d.getDate()}</span>
                  {acts.slice(0, 3).map((a) => (
                    <span key={a.id} className={claseChip(a.estado)}>{[horaCorta(a.hora), a.tarea].filter(Boolean).join(' · ')}</span>
                  ))}
                  {acts.length > 3 && <span className="cal-chip mas">+{acts.length - 3} más</span>}
                </div>
              })}
            </div>
          </div>
        )}

        {vista === 'semana' && (
          <div className="sem-grid">
            {fechasSemana(referencia).map((iso) => {
              const d = deISO(iso)
              const acts = chips(iso)
              return <div key={iso} className={`sem-col ${aISO(HOY) === iso ? 'hoy' : ''}`} onClick={() => setDiaSeleccionado(iso)}>
                <div className="sem-enc">{DIAS_CORTOS[(d.getDay() + 6) % 7]} {d.getDate()}</div>
                {acts.length === 0 && <span className="sem-vacio">Sin actividades</span>}
                {acts.map((a) => <span key={a.id} className={claseChip(a.estado)}>{[horaCorta(a.hora), a.tarea].filter(Boolean).join(' · ')}</span>)}
              </div>
            })}
          </div>
        )}

        {vista === 'dia' && (
          <>
            {chips(aISO(referencia)).length === 0 ? (
              <div className="empty"><CalendarDays size={28}/><strong>Sin actividades para este día</strong><span>Haga clic en "Nueva actividad" para programar una.</span>
                <button className="primary" onClick={() => setDiaSeleccionado(aISO(referencia))}><PlusCircle size={16}/>Nueva actividad</button>
              </div>
            ) : (
              <div className="agenda-cards">
                {chips(aISO(referencia)).map((act) => <TarjetaActividad key={act.id} act={act} onEstado={cambiarEstado}/>)}
              </div>
            )}
          </>
        )}
        <p className="fine-print">Haga clic en un día para ver el detalle y registrar actividades. Total en el rango consultado: {actividades.length}.</p>
      </section>
    )}
  </>
}
