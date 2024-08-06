
using UdonSharp;
using UnityEngine;
using VRC.SDK3.Image;
using VRC.SDKBase;
using VRC.Udon;
using VRC.Udon.Common.Interfaces;

namespace MikanDealer
{
	public enum LOADING_TYPE
	{
		[InspectorName("ぐるぐる")]
		GURUGURU = 0,
		[InspectorName("モザイク")]
		MOSIC = 1
	}

	public class SyncFrame : UdonSharpBehaviour
	{

		public string ID;
		public bool AutoAdjustAspect = true;
		public float FrameWidth = 0.1f;
		public LOADING_TYPE LoadingType = LOADING_TYPE.GURUGURU;
		//[HideInInspector]
		public VRCUrl Url;
		private int Retry = 0;

		void Start()
		{
			var renderer = GetComponent<MeshRenderer>();
			if (renderer != null && !string.IsNullOrEmpty(Url.Get()) && renderer.sharedMaterial != null)
			{
				var downloader = new VRCImageDownloader();
				if (renderer.sharedMaterial.mainTexture == null)
				{
					renderer.sharedMaterial.SetInt("_LoadingType", (int)LoadingType);
					renderer.sharedMaterial.SetFloat("_Progress", 0);
				}
				downloader.DownloadImage(Url, renderer.sharedMaterial, (IUdonEventReceiver)this);
				Retry += 1;
			}
		}

		override public void OnImageLoadSuccess(IVRCImageDownload download)
		{
			if (AutoAdjustAspect)
			{
				AdjustTexture(download.Result, 1);
			}
			else
			{
				DoneTexture(download.Result, 1);
			}
		}

		override public void OnImageLoadError(IVRCImageDownload download)
		{
			if (download.Error != VRCImageDownloadError.DownloadError && download.Error == VRCImageDownloadError.Unknown) return;
			if (Retry >= 2) return;

			var renderer = GetComponent<MeshRenderer>();
			if (renderer == null) return;
			var downloader = new VRCImageDownloader();
			downloader.DownloadImage(Url, renderer.sharedMaterial, (IUdonEventReceiver)this);
			Retry += 1;
		}

		public void AssignLoading()
		{
			var renderer = GetComponent<MeshRenderer>();
			if (renderer != null && renderer.sharedMaterial != null && renderer.sharedMaterial.mainTexture == null)
			{
				renderer.sharedMaterial.SetInt("_LoadingType", (int)LoadingType);
				renderer.sharedMaterial.SetFloat("_Progress", 0);
			}
		}

		public void Update()
		{
			var renderer = GetComponent<MeshRenderer>();
			if (renderer != null)
			{
				float p = renderer.sharedMaterial.GetFloat("_Progress");
				if (p <= 0 || p >= 2) return;
				p += 0.05f;
				if (p > 2.0) p = 2.0f;
				renderer.sharedMaterial.SetFloat("_Progress", p);
			}
		}

		public void DoneTexture(Texture2D tex, float progress)
		{
			var renderer = GetComponent<MeshRenderer>();
			if (renderer == null) return;
			renderer.sharedMaterial.SetFloat("_Progress", progress);
		}

		public void AdjustTexture(Texture2D tex, float progress)
		{
			float baseScale = 1;
			Vector3 scale;
			if (gameObject.transform.localScale.x > baseScale) baseScale = gameObject.transform.localScale.x;
			if (gameObject.transform.localScale.y > baseScale) baseScale = gameObject.transform.localScale.y;
			if (gameObject.transform.localScale.z > baseScale) baseScale = gameObject.transform.localScale.z;

			if (tex.height > tex.width)
			{
				scale = new Vector3((float)tex.width / (float)tex.height, 1, 1);
			}
			else
			{
				scale = new Vector3(1, (float)tex.height / (float)tex.width, 1);
			}
			gameObject.transform.localScale = scale * baseScale;

			var renderer = GetComponent<MeshRenderer>();
			if (renderer != null)
			{
				renderer.sharedMaterial.SetFloat("_Progress", progress);
				renderer.sharedMaterial.SetFloat("_ScaleX", 1 + scale.y * FrameWidth);
				renderer.sharedMaterial.SetFloat("_ScaleY", 1 + scale.x * FrameWidth);
			}
		}
	}
}