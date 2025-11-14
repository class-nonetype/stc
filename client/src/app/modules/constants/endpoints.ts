const authenticationRoute = 'authentication';
const applicationRoute = 'application';


export const endpoints = {

  authentication: {
    signIn: `${authenticationRoute}/sign-in`,
    signUp: `${authenticationRoute}/sign-up`,
    signOut: `${authenticationRoute}/sign-out`,
    refreshToken: `${authenticationRoute}/refresh-token`,
  },

  tickets: {
    base: `${applicationRoute}/tickets`,
    create: `${applicationRoute}/create/ticket`,
    byId: (ticketId: string) => `ticket/${ticketId}`,
    byRequester: (requesterId: string) => `${applicationRoute}/select/all/tickets/requester/${requesterId}`,
    byAssignee: (assigneeId: string) => `${applicationRoute}/select/all/tickets/assignee/${assigneeId}`,
    countByRequester: (requesterId: string) => `${applicationRoute}/select/total/tickets/requester/${requesterId}`,
    countByAssignee: (assigneeId: string) => `${applicationRoute}/select/total/tickets/assignee/${assigneeId}`,
  },

  userTeam: {
    base: `${applicationRoute}/select/all/teams`,
  },

  types: {
    requestTypes: `${applicationRoute}/select/all/request-types`,
    priorityTypes: `${applicationRoute}/select/all/priority-types`,
    statusTypes: `${applicationRoute}/select/all/status-types`,
    supportUsers: `${applicationRoute}/select/all/support-users`,
  }



} as const;
