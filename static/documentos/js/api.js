// static/panel/js/documentos/api.js
export const listUrl   = "/api/documentos/list/";    // antes: /app/documentos/api/list/
export const uploadUrl = "/api/documentos/upload/";  // antes: /app/documentos/api/upload/

export function getCookie(name){
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
}
export const csrftoken = getCookie("csrftoken");