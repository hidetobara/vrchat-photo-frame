Shader "MikanDealer/PhotoFrame"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _ScaleX("ScaleX", Float) = 1.1
        _ScaleY("ScaleY", Float) = 1.1
        _CellSize("Cell Size", Float) = 30.0
        _Color("Color", Color) = (0.5, 0.5, 0.5, 1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100

        CGINCLUDE

            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float _ScaleX;
            float _ScaleY;
            float _CellSize;
            fixed4 _Color;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : NORMAL;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

        ENDCG

        Pass
        {
            Cull Off

            CGPROGRAM

            float2 random2(float2 st)
            {
                st = float2(dot(st, float2(127.1, 311.7)),
                            dot(st, float2(269.5, 183.3)));
                return frac(sin(st) * 43758.5453123);
            }

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = mul(UNITY_MATRIX_VP, mul(UNITY_MATRIX_M, v.vertex * float4(_ScaleX, _ScaleY, 1, 1)) - float4(v.normal * 0.03, 0));
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float2 st = i.uv * _CellSize;
                float2 ist = floor(st);
                float2 fst = frac(st);

                float distance = 10000;
                float2 p_min = float2(0, 0);

                for (int y = -1; y <= 1; y++)
                for (int x = -1; x <= 1; x++)
                {
                    float2 neighbor = float2(x, y);
                    float2 p = random2(ist + neighbor);
                    float2 diff = neighbor + p - fst;

                    if(distance > length(diff)){
                        distance = length(diff);
                        p_min = p;
                    }
                }

                float brightness = (1 - pow(distance, 1.2)) * 0.05;
                return fixed4(
                    frac(sin(p_min.x * 456 + p_min.y * 564)) * brightness,
                    frac(sin(p_min.x * 234 + p_min.y * 342)) * brightness,
                    frac(sin(p_min.x * 345 + p_min.y * 453)) * brightness,
                    1) + _Color;
            }
            ENDCG
        }

        Pass
        {
            Cull Back

            CGPROGRAM

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
#ifdef UNITY_UV_STARTS_AT_TOP
                return tex2D(_MainTex, i.uv);
#else
                return float2(i.uv.x, 1 - i.uv.y);
#endif
            }
            ENDCG
        }
    }
}
