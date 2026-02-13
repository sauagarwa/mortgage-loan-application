{{/*
Expand the name of the chart.
*/}}
{{- define "mortgage-ai.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "mortgage-ai.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mortgage-ai.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mortgage-ai.labels" -}}
helm.sh/chart: {{ include "mortgage-ai.chart" . }}
{{ include "mortgage-ai.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mortgage-ai.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mortgage-ai.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mortgage-ai.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mortgage-ai.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image name helper
*/}}
{{- define "mortgage-ai.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- $repository := .Values.global.imageRepository -}}
{{- $name := .name -}}
{{- $tag := .tag | default .Values.global.imageTag -}}
{{- printf "%s/%s/%s:%s" $registry $repository $name $tag -}}
{{- end }}

{{/*
API labels
*/}}
{{- define "mortgage-ai.api.labels" -}}
{{ include "mortgage-ai.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "mortgage-ai.api.selectorLabels" -}}
{{ include "mortgage-ai.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
UI labels
*/}}
{{- define "mortgage-ai.ui.labels" -}}
{{ include "mortgage-ai.labels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "mortgage-ai.ui.selectorLabels" -}}
{{ include "mortgage-ai.selectorLabels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
Database labels
*/}}
{{- define "mortgage-ai.database.labels" -}}
{{ include "mortgage-ai.labels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
Database selector labels
*/}}
{{- define "mortgage-ai.database.selectorLabels" -}}
{{ include "mortgage-ai.selectorLabels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
Migration labels
*/}}
{{- define "mortgage-ai.migration.labels" -}}
{{ include "mortgage-ai.labels" . }}
app.kubernetes.io/component: migration
{{- end }}

{{/*
Migration selector labels
*/}}
{{- define "mortgage-ai.migration.selectorLabels" -}}
{{ include "mortgage-ai.selectorLabels" . }}
app.kubernetes.io/component: migration
{{- end }}
