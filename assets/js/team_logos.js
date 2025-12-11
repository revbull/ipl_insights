/* -------------------------------------------
   TEAM LOGO LIBRARY (IPL, BBL, PSL, SA20, ILT20)
-------------------------------------------- */

const TEAM_LOGOS = {

  /* ---------------- IPL ---------------- */
  "Mumbai Indians": "assets/logos/mi.png",
  "Chennai Super Kings": "assets/logos/csk.png",
  "Royal Challengers Bangalore": "assets/logos/rcb.png",
  "Bengaluru FC": "assets/logos/rcb.png",
  "Delhi Capitals": "assets/logos/dc.png",
  "Kolkata Knight Riders": "assets/logos/kkr.png",
  "Rajasthan Royals": "assets/logos/rr.png",
  "Sunrisers Hyderabad": "assets/logos/srh.png",
  "Lucknow Super Giants": "assets/logos/lsg.png",
  "Gujarat Titans": "assets/logos/gt.png",
  
  /* ---------------- BBL ---------------- */
  "Sydney Sixers": "assets/logos/sydney_sixers.png",
  "Sydney Thunder": "assets/logos/sydney_thunder.png",
  "Melbourne Stars": "assets/logos/melbourne_stars.png",
  "Melbourne Renegades": "assets/logos/melbourne_renegades.png",
  "Brisbane Heat": "assets/logos/brisbane_heat.png",
  "Hobart Hurricanes": "assets/logos/hobart_hurricanes.png",
  "Perth Scorchers": "assets/logos/perth_scorchers.png",
  "Adelaide Strikers": "assets/logos/adelaide_strikers.png",

  /* ---------------- PSL ---------------- */
  "Lahore Qalandars": "assets/logos/lq.png",
  "Karachi Kings": "assets/logos/kk.png",
  "Islamabad United": "assets/logos/iu.png",
  "Peshawar Zalmi": "assets/logos/pz.png",
  "Quetta Gladiators": "assets/logos/quetta.png",
  "Multan Sultans": "assets/logos/multan.png",

  /* ---------------- SA20 ---------------- */
  "Joburg Super Kings": "assets/logos/jsk.png",
  "Pretoria Capitals": "assets/logos/pc.png",
  "Sunrisers Eastern Cape": "assets/logos/sec.png",
  "MI Cape Town": "assets/logos/mict.png",
  "Paarl Royals": "assets/logos/pr.png",
  "Durban Super Giants": "assets/logos/dsg.png",

  /* ---------------- ILT20 ---------------- */
  "MI Emirates": "assets/logos/mi_emirates.png",
  "Desert Vipers": "assets/logos/desert_vipers.png",
  "Gulf Giants": "assets/logos/gulf_giants.png",
  "Sharjah Warriors": "assets/logos/sharjah_warriors.png",
  "Dubai Capitals": "assets/logos/dubai_capitals.png",
  "Abu Dhabi Knight Riders": "assets/logos/adkr.png",

  /* ------------ FALLBACK ------------ */
  "default": "assets/logos/default.png"
};


/* -------------------------------------------
   LOGO SELECTOR FUNCTION
-------------------------------------------- */
function getLogo(teamName) {
  if (!teamName) return TEAM_LOGOS["default"];

  // Exact match
  if (TEAM_LOGOS[teamName]) return TEAM_LOGOS[teamName];

  // Loose match (e.g., "MI Emirates (ILT20)" → finds "MI Emirates")
  const key = Object.keys(TEAM_LOGOS).find(k => teamName.includes(k));
  return key ? TEAM_LOGOS[key] : TEAM_LOGOS["default"];
}


