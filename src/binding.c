// SPDX-License-Identifier: MIT
#include "sl-common.h"
static bool test_controls;
static void forwarded(void *closure, int status, unsigned n, afb_data_t const replies[], afb_req_t req) {
    (void)closure;
    for(unsigned i=0;i<n;i++) afb_data_addref(replies[i]);
    afb_req_reply(req,status,n,replies);
}
static void proxy(afb_req_t req, unsigned n, afb_data_t const p[], const char *api, const char *verb) {
    for(unsigned i=0;i<n;i++) afb_data_addref(p[i]);
    /* Keep the originating client session for per-client subscriptions. */
    afb_req_subcall(req,api,verb,n,p,afb_req_subcall_pass_events,forwarded,NULL);
}
static void get_state(afb_req_t r,unsigned n,afb_data_t const p[]) { proxy(r,n,p,"sameloop-controller","get"); }
static void settings(afb_req_t r,unsigned n,afb_data_t const p[]) { proxy(r,n,p,"sameloop-controller","settings"); }
static void subscribe(afb_req_t r,unsigned n,afb_data_t const p[]) { proxy(r,n,p,"sameloop-controller","subscribe"); }
static void unsubscribe(afb_req_t r,unsigned n,afb_data_t const p[]) { proxy(r,n,p,"sameloop-controller","unsubscribe"); }
static void fault(afb_req_t r,unsigned n,afb_data_t const p[]) {
    if(!test_controls) { sl_error(r,-EPERM,"test controls disabled; opt in via binding config"); return; }
    proxy(r,n,p,"sameloop-sensor","fault");
}
static int ctl(afb_api_t api,afb_ctlid_t id,afb_ctlarg_t arg,void *data) {
    (void)data;
    if(id==afb_ctlid_Pre_Init && arg && arg->pre_init.config) {
        json_object *config=arg->pre_init.config;
        json_object *v=sl_get(config,"test_controls");
        if(v && !json_object_is_type(v,json_type_boolean)) return -EINVAL;
        test_controls=v && json_object_get_boolean(v);
    }
    if(id==afb_ctlid_Init) AFB_API_NOTICE(api,"SameLoop API ready; test controls=%d",test_controls);
    return 0;
}
static const afb_verb_t verbs[]={
    {.verb="get", .callback=get_state, .info="Read state"},
    {.verb="settings", .callback=settings, .info="Set mode OFF/AUTO and/or setpoint 15..40"},
    {.verb="subscribe", .callback=subscribe, .info="Subscribe to sameloop-controller/state; returns snapshot"},
    {.verb="unsubscribe", .callback=unsubscribe, .info="Unsubscribe this client"},
    {.verb="fault", .callback=fault, .info="Opt-in simulation controls; disabled by default"}, {0}
};
const afb_binding_t afbBindingV4={
    .api="sameloop-api", .verbs=verbs, .mainctl=ctl,
    .require_api="sameloop-controller", .noconcurrency=1,
    .info="SameLoop public UI API"
};
