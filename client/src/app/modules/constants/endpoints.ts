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
    postTicket: `${applicationRoute}/create/ticket`,
    getAllTicketsByRequesterUserId: (requesterId: string) => `${applicationRoute}/select/all/tickets/requester/${requesterId}`,
    //byAssignee: (assigneeId: string) => `${applicationRoute}/select/all/tickets/assignee/${assigneeId}`,
    getAllTicketsByManagerUser: `${applicationRoute}/select/all/tickets/manager`,
    getTotalTicketsByRequesterUserId: (requesterId: string) => `${applicationRoute}/select/total/tickets/requester/${requesterId}`,
    //countByAssignee: (assigneeId: string) => `${applicationRoute}/select/total/tickets/assignee/${assigneeId}`,
    getTotalTicketsByManagerUser: `${applicationRoute}/select/total/tickets/manager`
  },

  userTeam: {
    base: `${applicationRoute}/select/all/teams`,
  },

  types: {
    requestTypes: `${applicationRoute}/select/all/types/request`,
    priorityTypes: `${applicationRoute}/select/all/types/priority`,
    statusTypes: `${applicationRoute}/select/all/types/status`,
    supportUsers: `${applicationRoute}/select/all/users/support`,
  }



} as const;
