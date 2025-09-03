// static/panel/js/documentos/api.js
export const listUrl = "/app/documentos/api/list/";
export const uploadUrl = "/app/documentos/api/upload/";

export function getCookie(name){
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
}
export const csrftoken = getCookie("csrftoken");
