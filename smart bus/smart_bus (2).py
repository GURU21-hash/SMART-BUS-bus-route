"""
Smart Bus - Bus Route & Passenger Management System (Tamil Nadu)  |  Problem PL048
-------------------------------------------------------------------------------
Pure-Python engine + command-line menu. No external packages needed.

    python smart_bus.py            # interactive menu
    python smart_bus.py --selftest # quick automatic test of every feature

Covers: bus management (add / view / search / update / delete), route management
(add route / add stops / update route / search route), passenger management (book,
cancel, calculate fare, view passengers), the Bus Status Report, and the bonus
features (dynamic fare, route search, passenger load analysis, peak-hour analysis).

Notes: fares are APPROXIMATE (per-km rates); distances are map distance x 1.25 road
factor; payment is a demo; data is saved in smart_bus_data.json.
"""
import json, math, os, random, sys
from datetime import datetime

DATA_FILE = os.environ.get("SMARTBUS_DATA", "smart_bus_data.json")

# Bus-stand statistics supplied by the team (verify with the Municipal Administration Dept).
BUS_STAND_STATS = {"total": 184, "corporations": 43, "municipalities": 141,
                   "grades": {"A": 35, "B": 53, "C": 68, "D": 28}}
assert (BUS_STAND_STATS["corporations"] + BUS_STAND_STATS["municipalities"]
        == BUS_STAND_STATS["total"] == sum(BUS_STAND_STATS["grades"].values()))

# Approximate government rates - confirm on tnstc.in before publishing.
SERVICE_TYPES = {
    "Town/Mofussil Ordinary":   dict(per_km=0.60, min=5,   toll=False, res=0,  max_km=160, women_free=True),
    "TNSTC Express":            dict(per_km=0.80, min=15,  toll=True,  res=0,  max_km=None, women_free=False),
    "Point-to-Point Superfast": dict(per_km=0.95, min=25,  toll=True,  res=0,  max_km=None, women_free=False),
    "SETC Ultra Deluxe":        dict(per_km=1.20, min=40,  toll=True,  res=10, max_km=None, women_free=False),
    "SETC AC Sleeper":          dict(per_km=1.90, min=100, toll=True,  res=20, max_km=None, women_free=False),
}
SCHEMES = [
    ("Free travel for women and transgender persons", "Town/Mofussil ordinary buses, valid ID required"),
    ("Senior citizen concession", "Concession token/pass in town buses"),
    ("Student bus pass", "Concession passes issued through the institution"),
    ("Differently-abled concession", "Concession with disability ID"),
    ("Children", "Below 3 years free; half fare for 3-12 years"),
    ("Free luggage", "Personal luggage up to 25 kg in ordinary buses"),
]
HELPLINES = {"Emergency": "112", "Police": "100", "Fire": "101", "Ambulance": "108",
             "Women helpline": "1091", "Childline": "1098", "TNSTC toll-free": "1800 599 1500"}

# (name, latitude, longitude, district) - add more stands here or through add_stand().
STANDS = [
    ('Chennai (CMBT)', 13.07, 80.2, 'Chennai'),
    ('Chennai (KCBT Kilambakkam)', 12.84, 80.07, 'Chengalpattu'),
    ('Chengalpattu', 12.69, 79.98, 'Chengalpattu'),
    ('Kanchipuram', 12.83, 79.7, 'Kancheepuram'),
    ('Tiruvallur', 13.14, 79.91, 'Tiruvallur'),
    ('Arakkonam', 13.08, 79.67, 'Ranipet'),
    ('Ranipet', 12.93, 79.33, 'Ranipet'),
    ('Vellore', 12.92, 79.13, 'Vellore'),
    ('Ambur', 12.79, 78.72, 'Tirupathur'),
    ('Tiruvannamalai', 12.23, 79.07, 'Tiruvannamalai'),
    ('Villupuram', 11.94, 79.49, 'Viluppuram'),
    ('Kallakurichi', 11.74, 78.96, 'Kallakurichi'),
    ('Cuddalore', 11.75, 79.77, 'Cuddalore'),
    ('Chidambaram', 11.4, 79.69, 'Cuddalore'),
    ('Mayiladuthurai', 11.1, 79.65, 'Mayiladuthurai'),
    ('Kumbakonam', 10.96, 79.38, 'Thanjavur'),
    ('Thanjavur', 10.79, 79.14, 'Thanjavur'),
    ('Pudukkottai', 10.38, 78.82, 'Pudukkottai'),
    ('Ariyalur', 11.14, 79.08, 'Ariyalur'),
    ('Perambalur', 11.23, 78.88, 'Perambalur'),
    ('Tiruchirappalli (Central)', 10.8, 78.69, 'Tiruchirappalli'),
    ('Karur', 10.96, 78.08, 'Karur'),
    ('Namakkal', 11.22, 78.17, 'Namakkal'),
    ('Salem (New Bus Stand)', 11.66, 78.15, 'Salem'),
    ('Krishnagiri', 12.52, 78.21, 'Krishnagiri'),
    ('Hosur', 12.74, 77.83, 'Krishnagiri'),
    ('Dharmapuri', 12.13, 78.16, 'Dharmapuri'),
    ('Erode (Central)', 11.34, 77.72, 'Erode'),
    ('Perundurai', 11.28, 77.58, 'Erode'),
    ('Bhavani', 11.45, 77.68, 'Erode'),
    ('Gobichettipalayam', 11.45, 77.44, 'Erode'),
    ('Sathyamangalam', 11.5, 77.24, 'Erode'),
    ('Kangeyam', 11.01, 77.56, 'Tiruppur'),
    ('Tiruppur', 11.11, 77.34, 'Tiruppur'),
    ('Avinashi', 11.19, 77.27, 'Tiruppur'),
    ('Udumalaipettai', 10.59, 77.25, 'Tiruppur'),
    ('Coimbatore (Gandhipuram)', 11.02, 76.97, 'Coimbatore'),
    ('Pollachi', 10.66, 77.01, 'Coimbatore'),
    ('Mettupalayam', 11.3, 76.94, 'Coimbatore'),
    ('Valparai', 10.33, 76.96, 'Coimbatore'),
    ('Coonoor', 11.35, 76.8, 'Nilgiris'),
    ('Ooty (Udhagamandalam)', 11.41, 76.7, 'Nilgiris'),
    ('Palani', 10.45, 77.52, 'Dindigul'),
    ('Dindigul', 10.36, 77.98, 'Dindigul'),
    ('Kodaikanal', 10.24, 77.49, 'Dindigul'),
    ('Madurai (Mattuthavani)', 9.94, 78.16, 'Madurai'),
    ('Theni', 10.01, 77.48, 'Theni'),
    ('Bodinayakanur', 10.01, 77.35, 'Theni'),
    ('Karaikudi', 10.07, 78.78, 'Sivagangai'),
    ('Sivakasi', 9.45, 77.8, 'Virudhunagar'),
    ('Virudhunagar', 9.59, 77.96, 'Virudhunagar'),
    ('Rajapalayam', 9.45, 77.55, 'Virudhunagar'),
    ('Tenkasi', 8.96, 77.31, 'Tenkasi'),
    ('Ramanathapuram', 9.37, 78.83, 'Ramanathapuram'),
    ('Rameswaram', 9.29, 79.31, 'Ramanathapuram'),
    ('Thoothukudi', 8.8, 78.14, 'Thoothukudi'),
    ('Tirunelveli (New Bus Stand)', 8.73, 77.7, 'Tirunelveli'),
    ('Nagercoil', 8.18, 77.43, 'Kanyakumari'),
    ('Kanyakumari', 8.08, 77.54, 'Kanyakumari'),
    ('Nagapattinam', 10.77, 79.84, 'Nagapattinam'),
    ('Puducherry (Interstate)', 11.93, 79.83, 'Interstate'),
    ('Bengaluru (Majestic, KA)', 12.98, 77.57, 'Interstate'),
    ('Mysuru (KA)', 12.3, 76.64, 'Interstate'),
    ('Tirupati (AP)', 13.63, 79.42, 'Interstate'),
    ('Thiruvananthapuram (KL)', 8.49, 76.95, 'Interstate'),
    ('Kochi (KL)', 9.98, 76.28, 'Interstate'),
    ('Palakkad (KL)', 10.78, 76.65, 'Interstate'),
]

STAND_INDEX = {n: (la, lo, d) for n, la, lo, d in STANDS}


def distance_km(a, b):
    """Approximate road distance: great-circle distance x 1.25."""
    (la1, lo1, _), (la2, lo2, _) = STAND_INDEX[a], STAND_INDEX[b]
    p = math.pi / 180
    h = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return max(1, round(12742 * math.asin(math.sqrt(h)) * 1.25))


def calc_fare(km, service):
    """Dynamic fare = base + toll + reservation fee, rounded up to the next Rs.5."""
    s = SERVICE_TYPES[service]
    base = max(s["min"], round(km * s["per_km"]))
    toll = min(40, (km // 60) * 8) if s["toll"] and km > 60 else 0
    total = math.ceil((base + toll + s["res"]) / 5) * 5
    return {"base": base, "toll": toll, "reservation": s["res"], "total": total}


def seed():
    def bus(i, reg, route, drv, cap, avail, status, svc, dep):
        return {"id": i, "reg": reg, "route": route, "driver": drv, "capacity": cap,
                "seats_taken": list(range(1, cap - avail + 1)), "status": status,
                "service": svc, "depart": dep}
    buses = [bus("BUS101", "TN-33-N-1101", "R12", "Murugan K", 50, 8, "Running", "SETC Ultra Deluxe", "06:30"),
             bus("BUS102", "TN-38-N-2210", "R12", "Selvam P", 52, 20, "Running", "TNSTC Express", "09:15"),
             bus("BUS201", "TN-01-AN-3120", "R20", "Ravi S", 30, 12, "Running", "SETC AC Sleeper", "21:30"),
             bus("BUS301", "TN-58-N-4410", "R30", "Arumugam T", 48, 5, "Running", "Point-to-Point Superfast", "07:45"),
             bus("BUS302", "TN-72-N-5521", "R30", "Kannan V", 52, 30, "Maintenance", "Town/Mofussil Ordinary", "13:00")]
    routes = {"R12": ["Erode (Central)", "Perundurai", "Tiruppur", "Avinashi", "Coimbatore (Gandhipuram)"],
              "R20": ["Chennai (KCBT Kilambakkam)", "Villupuram", "Tiruchirappalli (Central)",
                      "Madurai (Mattuthavani)", "Tirunelveli (New Bus Stand)"],
              "R30": ["Madurai (Mattuthavani)", "Dindigul", "Karur", "Namakkal", "Salem (New Bus Stand)"]}
    return {"buses": {b["id"]: b for b in buses}, "routes": routes, "tickets": {}, "extra_stands": []}


class SmartBus:
    """All business logic. Every method raises ValueError with a clear message on bad input."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.db = json.load(f)
        else:
            self.db = seed()
            self.save()
        for n, la, lo, d in self.db.get("extra_stands", []):
            STAND_INDEX[n] = (la, lo, d)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=1, ensure_ascii=False)

    # ---------- stands ----------
    def stand_names(self):
        return sorted(STAND_INDEX)

    def add_stand(self, name, lat, lng, district):
        if name in STAND_INDEX:
            raise ValueError("Stand already exists")
        STAND_INDEX[name] = (float(lat), float(lng), district)
        self.db["extra_stands"].append([name, float(lat), float(lng), district]); self.save()

    # ---------- bus management ----------
    @staticmethod
    def available(bus):
        return bus["capacity"] - len(bus["seats_taken"])

    def add_bus(self, bus_id, reg, route, driver, capacity, service, depart, status="Running"):
        if bus_id in self.db["buses"]:
            raise ValueError("Bus ID already exists")
        if int(capacity) <= 0:
            raise ValueError("Capacity must be positive")
        if service not in SERVICE_TYPES:
            raise ValueError("Unknown service type")
        self.db["buses"][bus_id] = {"id": bus_id, "reg": reg, "route": route, "driver": driver,
                                    "capacity": int(capacity), "seats_taken": [], "status": status,
                                    "service": service, "depart": depart}
        self.save()

    def view_buses(self):
        return list(self.db["buses"].values())

    def search_bus(self, q):
        q = q.lower()
        return [b for b in self.view_buses()
                if q in " ".join(str(b[k]) for k in ("id", "reg", "route", "driver", "status", "service")).lower()]

    def update_bus(self, bus_id, **fields):
        b = self._bus(bus_id)
        for k, v in fields.items():
            if k in b and k not in ("id", "seats_taken"):
                b[k] = int(v) if k == "capacity" else v
        if b["capacity"] < len(b["seats_taken"]):
            raise ValueError("Capacity is less than seats already booked")
        self.save()

    def delete_bus(self, bus_id):
        self._bus(bus_id)
        del self.db["buses"][bus_id]; self.save()

    def _bus(self, bus_id):
        if bus_id not in self.db["buses"]:
            raise ValueError(f"Bus {bus_id} not found")
        return self.db["buses"][bus_id]

    # ---------- route management ----------
    def _check_stops(self, stops):
        bad = [s for s in stops if s not in STAND_INDEX]
        if bad or len(stops) < 2:
            raise ValueError("Need at least 2 valid stops. Unknown: " + ", ".join(bad))

    def add_route(self, no, stops):
        if no in self.db["routes"]:
            raise ValueError("Route already exists")
        self._check_stops(stops); self.db["routes"][no] = list(stops); self.save()

    def add_stop(self, no, stop, position=None):
        self._check_stops([stop, stop])
        r = self.db["routes"][no]
        r.insert(len(r) if position is None else position, stop); self.save()

    def update_route(self, no, stops):
        if no not in self.db["routes"]:
            raise ValueError("Route not found")
        self._check_stops(stops); self.db["routes"][no] = list(stops); self.save()

    def search_route(self, q):
        q = q.lower()
        return {no: s for no, s in self.db["routes"].items() if q in no.lower() or any(q in x.lower() for x in s)}

    def find_services(self, src, dst):
        out = []
        for b in self.view_buses():
            r = self.db["routes"].get(b["route"], [])
            if src in r and dst in r and r.index(src) < r.index(dst) and b["status"] != "Maintenance":
                out.append(b)
        return out

    # ---------- passenger management ----------
    def quote(self, bus_id, src, dst, gender="Male"):
        b = self._bus(bus_id)
        km = distance_km(src, dst)
        f = calc_fare(km, b["service"])
        if gender in ("Female", "Transgender") and SERVICE_TYPES[b["service"]]["women_free"]:
            f = dict(f, total=0)
        return dict(f, km=km)

    def book_ticket(self, bus_id, src, dst, passengers, phone, pay_mode="UPI", travel_date=None):
        """passengers: list of {'name','age','gender'}. Returns the ticket dict (with PNR)."""
        b = self._bus(bus_id)
        r = self.db["routes"].get(b["route"], [])
        if b["status"] != "Running":
            raise ValueError("Bus is not running")
        if not (src in r and dst in r and r.index(src) < r.index(dst)):
            raise ValueError("This bus does not run from the source to the destination")
        if not 1 <= len(passengers) <= 6:
            raise ValueError("Book 1 to 6 passengers at a time")
        if len(passengers) > self.available(b):
            raise ValueError("Not enough seats available")
        if not (phone.isdigit() and len(phone) == 10):
            raise ValueError("Enter a valid 10-digit mobile number")
        free = [s for s in range(1, b["capacity"] + 1) if s not in b["seats_taken"]][:len(passengers)]
        paid = sum(self.quote(bus_id, src, dst, p.get("gender", "Male"))["total"] for p in passengers)
        pnr = "TN" + "".join(random.choice("0123456789") for _ in range(8))
        t = {"pnr": pnr, "bus": bus_id, "from": src, "to": dst, "date": travel_date or datetime.now().strftime("%Y-%m-%d"),
             "seats": free, "passengers": passengers, "phone": phone, "paid": paid, "pay_mode": pay_mode,
             "status": "Confirmed", "booked_at": datetime.now().isoformat(timespec="seconds")}
        b["seats_taken"] += free
        self.db["tickets"][pnr] = t; self.save()
        return t

    def cancel_ticket(self, pnr):
        t = self.db["tickets"].get(pnr)
        if not t or t["status"] != "Confirmed":
            raise ValueError("Ticket not found or already cancelled")
        b = self.db["buses"].get(t["bus"])
        if b:
            b["seats_taken"] = [s for s in b["seats_taken"] if s not in t["seats"]]
        t["status"], t["refund"] = "Cancelled", int(t["paid"] * 0.9)   # 10% cancellation charge
        self.save()
        return t

    def passenger_details(self, bus_id=None, pnr=None):
        ts = self.db["tickets"].values()
        return [t for t in ts if (not pnr or t["pnr"] == pnr) and (not bus_id or t["bus"] == bus_id)]

    # ---------- reports ----------
    def bus_status_report(self, bus_id):
        b = self._bus(bus_id)
        r = self.db["routes"].get(b["route"], ["-", "-"])
        return {"Bus ID": b["id"], "Route": b["route"], "Source": r[0], "Destination": r[-1],
                "Capacity": b["capacity"], "Passengers": len(b["seats_taken"]),
                "Available Seats": self.available(b), "Status": b["status"]}

    def load_analysis(self):
        rows = []
        for b in self.view_buses():
            pct = round(100 * len(b["seats_taken"]) / b["capacity"])
            rows.append({"bus": b["id"], "passengers": len(b["seats_taken"]), "capacity": b["capacity"],
                         "load_pct": pct, "level": "High" if pct > 85 else "Medium" if pct > 60 else "Low"})
        return sorted(rows, key=lambda r: -r["load_pct"])

    def peak_hour_analysis(self):
        hours = {h: 0 for h in range(24)}
        for b in self.view_buses():
            hours[int(b["depart"].split(":")[0])] += len(b["seats_taken"])
        peak = max(hours, key=hours.get)
        return hours, peak


def fare_table(km):
    return [(n, calc_fare(km, n)["total"]) for n, s in SERVICE_TYPES.items() if not s["max_km"] or km <= s["max_km"]]


def stand_stats_text():
    s = BUS_STAND_STATS
    g = s["grades"]
    return (f"Tamil Nadu Bus Stands\nTotal: {s['total']} bus stands\nCorporations: {s['corporations']}\n"
            f"Municipalities: {s['municipalities']}\nGrade A: {g['A']}  Grade B: {g['B']}  "
            f"Grade C: {g['C']}  Grade D: {g['D']}")


# ======================= command-line menu =======================
def ask(prompt, cast=str, default=None):
    while True:
        raw = input(prompt + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not raw and default is not None:
            return default
        try:
            return cast(raw)
        except ValueError:
            print("  Invalid input, try again.")


def pick_stand(label):
    q = ask(f"{label} (type part of a name)").lower()
    m = [n for n in sorted(STAND_INDEX) if q in n.lower()]
    if not m:
        print("  No match."); return pick_stand(label)
    for i, n in enumerate(m[:12], 1):
        print(f"  {i}. {n}")
    return m[ask("  Choose number", int) - 1]


def show_table(rows, cols):
    print("  " + " | ".join(f"{c:<14}" for c in cols))
    for r in rows:
        print("  " + " | ".join(f"{str(r[c])[:14]:<14}" for c in cols))


def menu(app):
    items = {
        "1": ("View buses", lambda: show_table(app.view_buses(), ["id", "reg", "route", "driver", "capacity", "status"])),
        "2": ("Add bus", lambda: app.add_bus(ask("Bus ID"), ask("Registration no."), ask("Route no."), ask("Driver"),
                                              ask("Capacity", int), ask("Service type " + str(list(SERVICE_TYPES)), str, "TNSTC Express"),
                                              ask("Departure HH:MM", str, "07:00"))),
        "3": ("Search bus", lambda: show_table(app.search_bus(ask("Search")), ["id", "reg", "route", "driver", "status"])),
        "4": ("Update bus", lambda: app.update_bus(ask("Bus ID"), **{ask("Field (driver/status/route/capacity/depart)"): ask("New value")})),
        "5": ("Delete bus", lambda: app.delete_bus(ask("Bus ID"))),
        "6": ("Add route", lambda: app.add_route(ask("Route no."), [pick_stand("Stop 1"), pick_stand("Stop 2")])),
        "7": ("Add stop to route", lambda: app.add_stop(ask("Route no."), pick_stand("Stop"))),
        "8": ("Search route", lambda: print(app.search_route(ask("Route no. or stop")))),
        "9": ("Book ticket", lambda: book_flow(app)),
        "10": ("Cancel ticket", lambda: print("  Refund Rs.", app.cancel_ticket(ask("PNR"))["refund"])),
        "11": ("View passenger details", lambda: [print(" ", t) for t in app.passenger_details(ask("Bus ID (blank=all)", str, "") or None)]),
        "12": ("Calculate fare", lambda: print(fare_table(distance_km(pick_stand("From"), pick_stand("To"))))),
        "13": ("Bus status report", lambda: [print(f"  {k}: {v}") for k, v in app.bus_status_report(ask("Bus ID", str, "BUS101")).items()]),
        "14": ("Passenger load analysis", lambda: show_table(app.load_analysis(), ["bus", "passengers", "capacity", "load_pct", "level"])),
        "15": ("Peak-hour analysis", lambda: print_peak(app)),
        "16": ("Bus stand statistics", lambda: print(stand_stats_text())),
    }
    while True:
        print("\n=== SMART BUS - Bus Route & Passenger Management System ===")
        for k, (name, _) in items.items():
            print(f" {k:>2}. {name}")
        print("  0. Exit   | Emergency: 112 Police 100 Fire 101 Ambulance 108")
        c = input("Choose: ").strip()
        if c == "0":
            break
        if c in items:
            try:
                items[c][1]()
            except (ValueError, KeyError, IndexError) as e:
                print("  Error:", e)


def book_flow(app):
    src, dst = pick_stand("From"), pick_stand("To")
    buses = app.find_services(src, dst)
    if not buses:
        print("  No running bus on that route."); return
    for b in buses:
        q = app.quote(b["id"], src, dst)
        print(f"  {b['id']} {b['service']} dep {b['depart']} Rs.{q['total']} ({q['km']} km) seats left {app.available(b)}")
    bid = ask("Bus ID")
    n = ask("Number of passengers", int, 1)
    pax = [{"name": ask(f"Passenger {i+1} name"), "age": ask("  age", int), "gender": ask("  gender (Male/Female/Transgender)", str, "Male")} for i in range(n)]
    t = app.book_ticket(bid, src, dst, pax, ask("Mobile (10 digits)"), ask("Pay by UPI/Card/NetBanking", str, "UPI"))
    print(f"  CONFIRMED PNR {t['pnr']} seats {t['seats']} paid Rs.{t['paid']}")


def print_peak(app):
    hours, peak = app.peak_hour_analysis()
    for h, n in hours.items():
        if n:
            print(f"  {h:02d}:00 {'#' * (n // 2)} {n}")
    print(f"  Peak hour: {peak:02d}:00")


def selftest():
    import tempfile
    app = SmartBus(os.path.join(tempfile.mkdtemp(), "t.json"))
    r = app.bus_status_report("BUS101"); assert (r["Capacity"], r["Passengers"], r["Available Seats"]) == (50, 42, 8), r
    app.add_bus("BUS999", "TN-00-X-0001", "R12", "Test", 40, "TNSTC Express", "10:00"); app.update_bus("BUS999", driver="New"); assert app.search_bus("new")
    app.delete_bus("BUS999")
    app.add_route("R99", ["Chennai (CMBT)", "Madurai (Mattuthavani)"]); app.add_stop("R99", "Salem (New Bus Stand)"); app.update_route("R99", ["Chennai (CMBT)", "Salem (New Bus Stand)"]); assert app.search_route("salem")
    t = app.book_ticket("BUS102", "Erode (Central)", "Coimbatore (Gandhipuram)", [{"name": "A", "age": 30, "gender": "Male"}], "9876543210")
    assert t["paid"] == calc_fare(distance_km("Erode (Central)", "Coimbatore (Gandhipuram)"), "TNSTC Express")["total"]
    before = app.available(app.db["buses"]["BUS102"]); assert app.cancel_ticket(t["pnr"])["refund"] > 0
    assert app.available(app.db["buses"]["BUS102"]) == before + 1
    assert app.load_analysis()[0]["load_pct"] >= app.load_analysis()[-1]["load_pct"]; assert app.peak_hour_analysis()[1] == 7
    print("SELFTEST OK |", r, "| fares 100 km:", fare_table(100))


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else menu(SmartBus())
