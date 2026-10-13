"""Smart Bus - Bus Route & Passenger Management System: Streamlit web interface.
Run:  pip install streamlit pandas   then   streamlit run streamlit_app.py
Uses the engine in smart_bus.py (same folder). Payment is a demo; fares are approximate."""
import pandas as pd
import streamlit as st
from smart_bus import (BUS_STAND_STATS, HELPLINES, SCHEMES, SERVICE_TYPES, STAND_INDEX, SmartBus,
                       calc_fare, distance_km, fare_table)

st.set_page_config(page_title="Smart Bus", page_icon="🚌", layout="wide")
app = SmartBus()
st.title("🚌 Smart Bus – Bus Route & Passenger Management System")
st.caption("Emergency: 112 · Police 100 · Fire 101 · Ambulance 108 · Women 1091 · TNSTC 1800 599 1500  |  "
           "[Google Maps](https://www.google.com/maps)")
stands = app.stand_names()
t_book, t_tix, t_buses, t_routes, t_rep, t_info = st.tabs(
    ["Book ticket", "My tickets", "Buses", "Routes", "Reports", "Fares, stands & schemes"])

with t_book:
    c1, c2 = st.columns(2)
    src = c1.selectbox("From", stands, index=stands.index("Erode (Central)"))
    dst = c2.selectbox("To", stands, index=stands.index("Coimbatore (Gandhipuram)"))
    if src != dst:
        st.write(f"Distance (approx.): **{distance_km(src, dst)} km**  ·  "
                 f"[Check on Google Maps](https://www.google.com/maps/dir/?api=1&origin={src.replace(' ', '+')}"
                 f"&destination={dst.replace(' ', '+')}&travelmode=driving)")
        buses = app.find_services(src, dst)
        if not buses:
            st.info("No running bus on this route yet. Add a route and bus in the other tabs.")
        for b in buses:
            q = app.quote(b["id"], src, dst)
            with st.expander(f"{b['id']} · {b['service']} · departs {b['depart']} · ₹{q['total']} · "
                             f"{app.available(b)} seats left"):
                n = st.number_input("Passengers", 1, 6, 1, key=f"cnt{b['id']}")
                with st.form(f"book_{b['id']}"):
                    pax = []
                    for i in range(int(n)):
                        a, bb, g = st.columns(3)
                        pax.append({"name": a.text_input("Name", key=f"n{b['id']}{i}"),
                                    "age": bb.number_input("Age", 1, 110, 25, key=f"a{b['id']}{i}"),
                                    "gender": g.selectbox("Gender", ["Male", "Female", "Transgender"], key=f"g{b['id']}{i}")})
                    phone = st.text_input("Mobile number (10 digits)", key=f"p{b['id']}")
                    mode = st.radio("Pay with (demo)", ["UPI", "Card", "Net banking"], horizontal=True, key=f"m{b['id']}")
                    if st.form_submit_button("Pay and book"):
                        try:
                            if not all(p["name"].strip() for p in pax):
                                raise ValueError("Enter every passenger's name")
                            t = app.book_ticket(b["id"], src, dst, pax, phone, mode)
                            st.success(f"Confirmed! PNR {t['pnr']} · seats {t['seats']} · paid ₹{t['paid']}")
                            st.balloons()
                        except ValueError as e:
                            st.error(str(e))

with t_tix:
    rows = list(app.db["tickets"].values())
    st.dataframe(pd.DataFrame(rows).drop(columns=["passengers"], errors="ignore") if rows else pd.DataFrame())
    pnr = st.text_input("PNR to cancel")
    if st.button("Cancel ticket"):
        try:
            st.success(f"Cancelled. Refund ₹{app.cancel_ticket(pnr.strip())['refund']} (10% charge)")
        except ValueError as e:
            st.error(str(e))

with t_buses:
    q = st.text_input("Search bus by ID, registration, route or driver")
    st.dataframe(pd.DataFrame(app.search_bus(q)).drop(columns=["seats_taken"], errors="ignore"))
    with st.form("add_bus"):
        st.subheader("Add bus")
        a, b, c = st.columns(3)
        bid, reg, route = a.text_input("Bus ID"), b.text_input("Registration no."), c.text_input("Route no.")
        d, e, f = st.columns(3)
        drv, cap, svc = d.text_input("Driver"), e.number_input("Capacity", 1, 80, 50), f.selectbox("Service", list(SERVICE_TYPES))
        dep = st.text_input("Departure (HH:MM)", "07:00")
        if st.form_submit_button("Add bus"):
            try:
                app.add_bus(bid, reg, route, drv, cap, svc, dep); st.success("Bus added"); st.rerun()
            except ValueError as ex:
                st.error(str(ex))
    ids = [b["id"] for b in app.view_buses()]
    if ids:
        sel = st.selectbox("Update or delete bus", ids)
        u1, u2, u3 = st.columns(3)
        new_drv = u1.text_input("New driver")
        new_status = u2.selectbox("Status", ["Running", "Stopped", "Maintenance"])
        if u3.button("Update"):
            app.update_bus(sel, status=new_status, **({"driver": new_drv} if new_drv else {})); st.rerun()
        if u3.button("Delete bus"):
            app.delete_bus(sel); st.rerun()

with t_routes:
    st.dataframe(pd.DataFrame([{"Route": k, "Stops": " → ".join(v)} for k, v in app.db["routes"].items()]))
    with st.form("route"):
        no = st.text_input("Route no. (existing number = update)")
        stops = st.multiselect("Stops in order", stands)
        if st.form_submit_button("Save route"):
            try:
                (app.update_route if no in app.db["routes"] else app.add_route)(no, stops); st.success("Saved"); st.rerun()
            except ValueError as ex:
                st.error(str(ex))
    with st.form("stand"):
        st.subheader("Add a village / town bus stand (coordinates from Google Maps)")
        n, la, lo, di = st.columns(4)
        name, lat, lng, dist = n.text_input("Name"), la.number_input("Latitude", 8.0, 14.0, 11.0), lo.number_input("Longitude", 76.0, 80.5, 78.0), di.text_input("District")
        if st.form_submit_button("Add stand"):
            try:
                app.add_stand(name, lat, lng, dist); st.success("Added"); st.rerun()
            except ValueError as ex:
                st.error(str(ex))

with t_rep:
    sel = st.selectbox("Bus status report", [b["id"] for b in app.view_buses()])
    st.table(pd.DataFrame([app.bus_status_report(sel)]).T.rename(columns={0: "Value"}))
    st.subheader("Passenger load analysis")
    st.dataframe(pd.DataFrame(app.load_analysis()))
    hours, peak = app.peak_hour_analysis()
    st.subheader(f"Peak-hour analysis – peak at {peak:02d}:00")
    st.bar_chart(pd.Series(hours, name="Passengers"))

with t_info:
    st.subheader("🚌 Tamil Nadu Bus Stands")
    s = BUS_STAND_STATS
    m = st.columns(3)
    m[0].metric("Total bus stands", s["total"]); m[1].metric("Corporations", s["corporations"]); m[2].metric("Municipalities", s["municipalities"])
    g = st.columns(4)
    for col, k in zip(g, "ABCD"):
        col.metric(f"Grade {k}", s["grades"][k])
    st.caption("Figures supplied by the team – verify with the Municipal Administration Dept (tnurbantree.tn.gov.in).")
    st.subheader("Fare per km (approximate – confirm on tnstc.in)")
    st.dataframe(pd.DataFrame([{"Service": n, "₹ per km": v["per_km"], "Minimum fare": v["min"],
                                "100 km": calc_fare(100, n)["total"]} for n, v in SERVICE_TYPES.items()]))
    st.subheader("Schemes")
    for n, d in SCHEMES:
        st.write(f"**{n}** – {d}")
    st.subheader("Helplines")
    st.table(pd.DataFrame(HELPLINES.items(), columns=["Service", "Number"]))
