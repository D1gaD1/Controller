<template>
  <v-app id="inspire">
    <v-main class="grey lighten-3">
      <v-form>
         <v-card>
            <v-card-text>
               <v-text-field label="Username"/>
               <v-text-field label="Password" type="password" />
            </v-card-text>
            <v-card-actions>
               <v-btn type="submit">
                  Login
               </v-btn>
            </v-card-actions>
         </v-card>
      </v-form>
    </v-main>
  </v-app>
</template>
